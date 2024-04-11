import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

"""
Implementation based on work by Nicholas Rhinehart, Panagiotis Tigkas, Angelos Filos,
    Kris M. Kitani, Paul Vernaza.

Reference paper: http://openaccess.thecvf.com/content_ECCV_2018/papers/Nicholas_Rhinehart_R2P2_A_ReparameteRized_ECCV_2018_paper.pdf  
"""

class R2P2(nn.Module):
    def __init__(self,
                 past_encoder_dim=32,
                 field_model_num_channels=32, 
                 field_model_num_layers=4,
                 mlp_hidden_layers=[512],
                 device='cuda:0'):
        super().__init__()

        assert field_model_num_layers > 0
        self.past_encoder_dim = past_encoder_dim
        
        # Define field model convolutional network.
        self.field_layers = [nn.ZeroPad2d((0,1,0,1)),
                             nn.Conv2d(2, 32, 2).to(device),
                             nn.ReLU()]
        for i in range(field_model_num_layers - 1):
            self.field_layers.append(
                nn.ZeroPad2d((0, 1, 0, 1)) # pad right and bottom
            )
            self.field_layers.append(
                nn.Conv2d(32,
                          32, # number of output channels
                          2, # kernel size
            ).to(device))
            self.field_layers.append(nn.ReLU())

        # Encoder and decoder GRUs.
        self.past_encoder = nn.GRU(2,
                                   past_encoder_dim,
                                   batch_first=True)
        self.future_decoder = nn.GRU(past_encoder_dim + 2, # Stacked context and y_tm1
                                     past_encoder_dim,
                                     batch_first=True)

        self.locscale_mlp_layers = [nn.Linear(past_encoder_dim, mlp_hidden_layers[0])]
        for i in range(1, len(mlp_hidden_layers)):
            self.locscale_mlp_layers.append(nn.Linear(mlp_hidden_layers[i-1],
                                               mlp_hidden_layers[i]))
            self.locscale_mlp_layers.append(nn.ReLU())
        self.locscale_mlp_layers.append(nn.Linear(mlp_hidden_layers[-1], 4))
        self.locscale_mlp = nn.Sequential(*self.locscale_mlp_layers)

        self.device = device

    def field_model(self, x):
        # Runs field model on input x (200 by 200 by 2).
        val = x
        # Puts output in (batch, channels, height, width) order
        val = val.permute(0, 3, 1, 2)
        for layer in self.field_layers:
            val = layer(val)
        val = val.permute(0, 2, 3, 1) # Puts back into original order.
        return val

    def forward(self, z, player_past, lidar):
        batch_size = player_past.shape[0]
        encoder_hidden = torch.zeros((1, batch_size, self.past_encoder_dim), device=self.device)

        context_past, encoder_hidden = self.past_encoder(player_past, encoder_hidden)

        encoded_context = context_past[:, -1, :] # Get the context from only the last time step
        future_state = encoded_context.unsqueeze(0)

        context_lidar = self.field_model(lidar)

        y_tm2 = player_past[:, -2:-1, :]
        y_tm1 = player_past[:, -1:, :]

        ys = []
        scales = []

        num_future_steps = z.shape[1]
        for t in range(num_future_steps):
            interp_t = self.interpolate_bilinear(
                           grid=context_lidar,
                           query_points=y_tm1)

            decoder_input = torch.cat([y_tm1, interp_t], axis=-1)

            h, future_state = self.future_decoder(decoder_input, future_state)
            loc_scale = self.locscale_mlp(h)

            loc = loc_scale[..., :2]
            scale = F.softplus(loc_scale[..., 2:])

            loc_verlet = self.verlet(loc, y_tm1, y_tm2)

            y_t = loc_verlet + scale * z[:,t:t+1,:]
            assert y_t.shape == y_tm1.shape

            ys.append(y_t)
            scales.append(scale)
            y_tm2 = y_tm1
            y_tm1 = y_t.float()

        y = torch.cat(ys, axis=1)
        scales = torch.cat(scales, axis=1)

        logabsdet = torch.log(torch.abs(torch.prod(scales, dim=-2)))
        logabsdet = torch.sum(logabsdet, dim=-1)
        
        return y, logabsdet

    def inverse(self, y, player_past, lidar):
        batch_size = player_past.shape[0]
        encoder_hidden = torch.zeros((1, batch_size, self.past_encoder_dim), device=self.device)

        context_past, encoder_hidden = self.past_encoder(player_past, encoder_hidden)
        encoded_context = context_past[:, -1, :] # Last time step
        future_state = encoded_context.unsqueeze(0)

        context_lidar = self.field_model(lidar)

        y_tm2 = player_past[:, -2:-1, :]
        y_tm1 = player_past[:, -1:, :]

        xs = []
        scales = []

        for t in range(y.shape[1]): # number of future time steps
            interp_t = self.interpolate_bilinear(
                           grid=context_lidar,
                           query_points=y_tm1)

            decoder_input = torch.cat([y_tm1, interp_t], axis=-1)

            h, future_state = self.future_decoder(decoder_input, future_state)
            loc_scale = self.locscale_mlp(h)

            loc = loc_scale[..., :2]
            scale = F.softplus(loc_scale[..., 2:])

            loc_verlet = self.verlet(loc, y_tm1, y_tm2)

            y_t = y[:, t:t+1,:]
            x_t = (y_t - loc_verlet) / scale

            xs.append(x_t)
            scales.append(scale)
            y_tm2 = y_tm1
            y_tm1 = y_t.float()

        x = torch.cat(xs, axis=1)
        scales = torch.cat(scales, axis=1)

        logabsdet = torch.log(torch.abs(torch.prod(scales, dim=-1)))
        logabsdet = torch.sum(logabsdet, dim=-1)
        
        return x, logabsdet

    def verlet(self, a_t, y_tm1, y_tm2):
        """
        a_t: the acceleration variable, with shape
          `[batch_size, 1, 2]`.
        y_tm1: the positions at time `t-1`, with shape
          `[batch_size, 1, 2]`.
        y_tm2: the positions at time `t-2`, with shape
          `[batch_size, 1, 2]`.

        Returns:
          The position at time `t`, with shape `[batch_size, 1, 2]`.
        """
        return 2 * y_tm1 - y_tm2 + a_t

    def interpolate_bilinear(self, grid, query_points):
        """
        grid: a [batch_size, height, width, channels] Tensor
        query_points: a [batch_size, num_points, 2] Tensor
    
        Returns:
            A [batch_size, num_points, channels] Tensor
        """

        assert len(grid.shape) == 4, "Grid shape must be 4-dimensional"
        assert len(query_points.shape) == 3, "query_points must be 3-dimensional"
        assert query_points.shape[2] == 2
        assert grid.shape[1] >= 2
        assert grid.shape[2] >= 2
        
        batch_size, height, width, channels = grid.shape
        num_queries = query_points.shape[1]

        alphas, floors, ceils = [], [], []

        for dim in range(2):
            queries = query_points[:, :, dim]
            floor = torch.floor(queries)
            # Threshold values to between min_floor and max_floor
            max_floor = grid.shape[dim+1] - 2 # To make sure ceil is still valid
            min_floor = 0.0
            min_mask = (floor >= min_floor)
            floor = floor * min_mask + min_floor * (torch.logical_not(min_mask))
            max_mask = (floor <= max_floor)
            floor = floor * max_mask + max_floor * (torch.logical_not(max_mask))
            floor = floor.to(torch.int32)
            floors.append(floor)
            ceils.append(floor + 1)

            alpha = queries - floor
            # Threshold alpha values to between 0 and 1
            alpha = alpha * (alpha >= 0)
            alpha = alpha * (alpha <= 1) + (torch.logical_not(alpha <= 1))
            alpha = alpha.unsqueeze(-1)
            assert alpha.shape == (batch_size, num_queries, 1)
            alphas.append(alpha)

        flattened_grid = torch.reshape(grid, (batch_size * height * width, channels))
        batch_offsets = torch.tensor(np.arange(batch_size) * height * width, device=self.device).unsqueeze(-1)

        def gather_pixels(y_coords, x_coords):
            linear_coordinates = (batch_offsets + y_coords * width + x_coords).to(torch.int64)
            gathered_values = flattened_grid[linear_coordinates[:,0]] 
            return torch.reshape(gathered_values, [batch_size, num_queries, channels])

        top_left = gather_pixels(floors[0], floors[1])
        top_right = gather_pixels(floors[0], ceils[1])
        bottom_left = gather_pixels(ceils[0], floors[1])
        bottom_right = gather_pixels(ceils[0], ceils[1])

        interp_top = alphas[1] * (top_right - top_left) + top_left
        interp_bottom = alphas[1] * (bottom_right - bottom_left) + bottom_left
        interpolated = alphas[0] * (interp_bottom - interp_top) + interp_top
        
        assert interpolated.shape == (batch_size, num_queries, channels)
        return interpolated

    def loss(self, player_past, lidar, player_future):
        zs, logabsdet = self.inverse(player_future, player_past, lidar)
        n = torch.distributions.Normal(0.0, 1.0)
        loss = torch.sum(n.log_prob(zs))
        loss -= torch.sum(logabsdet)

        return -loss

