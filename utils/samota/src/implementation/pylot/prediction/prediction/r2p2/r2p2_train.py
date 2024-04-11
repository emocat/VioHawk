from r2p2_model import R2P2

from absl import app, flags
from glob import glob
import json
import numpy as np
import os
import torch
import tqdm

flags.DEFINE_string('r2p2_train_data', '', 'Path to r2p2 training data.')
flags.DEFINE_string('r2p2_val_data', '', 'Path to r2p2 validation data.')

device = 'cuda'
FLAGS = flags.FLAGS

def load_file(f):
    json_datum = json.load(open(f, 'r'))
    datum = {}
    for k, v in json_datum.items():
        if isinstance(v, list):
            datum[k] = np.asarray(v)
        elif isinstance(v, dict) or isinstance(v, int) or isinstance(v, str):
            datum[k] = v
        else:
            raise ValueError("Unrecognized type")
    features = datum['overhead_features'].astype(np.float32)
    future = datum['player_future'][:, :2].astype(np.float32)
    past = datum['player_past'][:, :2].astype(np.float32)
    return [past, features, future]

def load_carla_dataset(dataset_path):
    filenames = list(glob(os.path.join(*[dataset_path, "*.*"])))
    past_list, features_list, future_list = [], [], []
    count = 0
    for filename in filenames:
        data = load_file(filename)
        past_list.append(data[0])
        features_list.append(data[1][:,:,1:3])
        future_list.append(data[2])	
        count += 1
        if count % 1000 == 0:
             print("Loaded {} files.".format(count))
    print ("Loaded {} files.".format(count))
    return torch.utils.data.TensorDataset(torch.FloatTensor(past_list),
                                          torch.FloatTensor(features_list),
                                          torch.FloatTensor(future_list))

def train(network, n_epochs=25, noise=1e-2, batch_size=64):
    # Load data.
    train_data = load_carla_dataset(FLAGS.r2p2_train_data)
    train_data_loader = torch.utils.data.DataLoader(train_data, batch_size=batch_size, shuffle=True)
    val_data = load_carla_dataset(FLAGS.r2p2_val_data)
    eval_data_loader = torch.utils.data.DataLoader(val_data, batch_size=batch_size, shuffle=False)

    optimizer = torch.optim.Adam(network.parameters())
    best_min_msd = 1000000

    for epoch in range(n_epochs):
        print ('Epoch', epoch)
        epoch_loss = 0.0
        for batch in tqdm.tqdm(train_data_loader, leave=True):
            optimizer.zero_grad()

            past_batch, features_batch, future_batch = batch
	        # Add noise to trajectories.
            past_batch += torch.tensor(np.random.normal(0, noise, past_batch.shape)).to(torch.float64)
            past_batch = torch.tensor(past_batch, device=device)

            features_batch = torch.tensor(features_batch, device=device)
            future_batch += torch.tensor(np.random.normal(0, noise, future_batch.shape)).to(torch.float64)
            future_batch = torch.tensor(future_batch, device=device)
            assert network.training

            loss = network.loss(past_batch, features_batch, future_batch)	
            loss.backward()
            optimizer.step()

            epoch_loss += loss
        print ('Loss: {}'.format(epoch_loss / len(train_data)))
        if epoch % 10 == 1:
            min_msd = evaluate(network, eval_data_loader)
            if min_msd < best_min_msd:
                print ('Better min_msd, saving network...')
                torch.save(network.state_dict(), "r2p2.pt")
                best_min_msd = min_msd
    # Evaluate at the end.
    min_msd = evaluate(network, eval_data_loader)
    # Save at the end if best.
    if min_msd < best_min_msd:
        torch.save(network.state_dict(), "r2p2.pt")

def min_msd(network, X, lidar, y, K=12):
    res = []
    network.training = False
    for i in range(K):
        z = torch.tensor(np.random.normal(size=(X.shape[0], y.shape[1], 2)),
                         device=device)
        res.append(network.forward(z, X, lidar)[0].detach().cpu().numpy())
    network.training = True

    res = np.stack(res, axis=0)
    y_exp = np.tile(np.expand_dims(y, axis=0), [K, 1, 1, 1])
    s_diff = res-y_exp
    s_diff_norm = np.linalg.norm(s_diff, axis=-1) # (K, batch_size, num_steps)
    return np.amin(np.mean(s_diff_norm, axis=2), axis=0)

def evaluate(network, eval_data_loader): 
    num_examples = len(eval_data_loader.dataset)
    total_min_msd = 0.0
    for batch in eval_data_loader:
        past, features, future = batch
        past, features = past.to(device), features.to(device)
        min_msds = (min_msd(network, past, features, future))
        # print (min_msds)
        total_min_msd += np.sum(min_msds)
    total_min_msd /= num_examples
    print ("Average MinMSD: {}".format(total_min_msd))
    return total_min_msd

def main(args):
    r2p2_network = R2P2().to(device)
    train(r2p2_network, n_epochs=1000, batch_size=64)

if __name__ == '__main__':
    app.run(main)
