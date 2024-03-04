import logging

from copy import deepcopy
from pathlib import Path
from typing import Tuple, List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import geopandas as gpd
import random
from commonroad.geometry.shape import Polygon
from commonroad.visualization.draw_params import MPDrawParams
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.visualization.util import LineDataUnits

import commonroad_reach.utility.logger as util_logger
from commonroad_reach.data_structure.reach.reach_interface import ReachableSetInterface
from commonroad_reach.utility.visualization import (
    compute_plot_limits_from_reachable_sets,
    generate_default_drawing_parameters,
    draw_reachable_sets,
    save_fig,
    make_gif,
)

logger = logging.getLogger(__name__)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)


def plot_polygons(polygons, polys2=None):
    fig, ax = plt.subplots()

    for i in range(len(polygons)):
        rcolor = "#" + hex(random.randint(0, 0xFFFFFF))[2:].rjust(6, "0")
        gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygons[i]]).plot(ax=ax, color=rcolor, aspect=1)

    if polys2:
        for i in range(len(polys2)):
            rcolor = "#" + hex(random.randint(0, 0xFFFFFF))[2:].rjust(6, "0")
            gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polys2[i]]).plot(
                ax=ax, color=rcolor, aspect=1, alpha=0.3
            )

    ax.set_aspect("auto")
    plt.savefig("/tmp/tmp.png")


def plot_scenario_with_reachable_sets(
    reach_interface_list: List[ReachableSetInterface],
    figsize: Tuple = None,
    step_start: int = 0,
    step_end: int = 0,
    steps: List[int] = None,
    plot_limits: List = None,
    path_output: str = None,
    save_gif: bool = True,
    duration: float = None,
    terminal_set=None,
    num_of_frame: int = 30,
    grid_line=None,
    danger_zone_list=None,
):
    """
    Plots scenario with computed reachable sets.
    """
    path_output = path_output or reach_interface_list[0].config.general.path_output
    Path(path_output).mkdir(parents=True, exist_ok=True)

    figsize = figsize if figsize else (25, 15)
    palette = sns.color_palette("GnBu_d", 3)
    edge_color = (palette[0][0] * 0.75, palette[0][1] * 0.75, palette[0][2] * 0.75)

    for reach_interface in reach_interface_list:
        tmp_plot_limits = compute_plot_limits_from_reachable_sets(reach_interface)
        # print(tmp_plot_limits)
        if plot_limits:
            plot_limits[0] = min(plot_limits[0], tmp_plot_limits[0])
            plot_limits[1] = max(plot_limits[1], tmp_plot_limits[1])
            plot_limits[2] = min(plot_limits[2], tmp_plot_limits[2])
            plot_limits[3] = max(plot_limits[3], tmp_plot_limits[3])
        else:
            plot_limits = tmp_plot_limits

    renderer = MPRenderer(plot_limits=plot_limits, figsize=figsize)

    count = 0
    for reach_interface in reach_interface_list:
        config = reach_interface.config
        scenario = config.scenario
        planning_problem = config.planning_problem
        ref_path = config.planning.reference_path

        # generate default drawing parameters
        draw_params = generate_default_drawing_parameters(config)
        draw_params.shape.facecolor = palette[0]
        draw_params.shape.edgecolor = edge_color

        step_start = step_start or reach_interface.step_start
        step_end = step_end or reach_interface.step_end
        if steps:
            steps = [step for step in steps if step <= step_end + 1]
        else:
            steps = range(step_start, step_end + 1)
        duration = duration if duration else config.planning.dt

        plt.figure(figsize=figsize)
        renderer = MPRenderer(plot_limits=plot_limits)

        # plot grid line
        if grid_line:
            for l in grid_line:
                tmp_vertices = np.array(l)
                collection = LineDataUnits(
                    tmp_vertices[:, 0],
                    tmp_vertices[:, 1],
                    zorder=12,
                    linewidth=0.5,
                    alpha=1.0,
                    color="blue",
                    linestyle="-",
                )
                renderer.static_artists.append(collection)

        # plot scenario and planning problem
        # print(step_start, step_end, steps, duration)
        draw_params.time_begin = 200 // num_of_frame
        scenario.draw(renderer, draw_params)

        if config.debug.draw_planning_problem:
            planning_problem.draw(renderer, draw_params)

        list_nodes = reach_interface.reachable_set_at_step(200 // num_of_frame)
        draw_reachable_sets(list_nodes, config, renderer, draw_params)

        # draw danger zone
        danger_poly = danger_zone_list[count]
        new_params = deepcopy(draw_params)
        new_params.facecolor = "red"
        new_params.opacity = 0.5
        if danger_poly:
            # danger polygon is curvelinear coordinate
            # list_polygons_cart = util_coordinate_system.convert_to_cartesian_polygons(danger_poly, config.planning.CLCS, True)
            # for polygon in list_polygons_cart:
            #     Polygon(vertices=np.array(polygon.vertices)).draw(renderer, new_params)

            # danger polygon is cartesian coordinate
            from shapely.geometry import MultiPolygon
            from shapely.ops import unary_union

            if isinstance(danger_poly, MultiPolygon):
                p = []
                for poly in danger_poly.geoms:
                    x, y = poly.exterior.coords.xy
                    area = np.array(list(zip(x, y)))
                    Polygon(vertices=area).draw(renderer, new_params)
            else:
                x, y = danger_poly.exterior.coords.xy
                area = np.array(list(zip(x, y)))
                Polygon(vertices=area).draw(renderer, new_params)

            # import mutator_rule
            # ego_position = config.planning_problem.initial_state.position
            # ego_polygon = mutator_rule.get_four_wheel_position(dict(x=ego_position[0], y=0, z=ego_position[1]), dict(x=0,y=config.planning_problem.initial_state.orientation, z=0))
            # Polygon(np.array(ego_polygon)).draw(renderer, new_params)

        # plot terminal set
        if terminal_set:
            draw_params_temp = MPDrawParams()
            draw_params_temp.shape.opacity = 1.0
            draw_params_temp.shape.linewidth = 0.5
            draw_params_temp.shape.facecolor = "#f1b514"
            draw_params_temp.shape.edgecolor = "#302404"
            draw_params_temp.shape.zorder = 15

            terminal_set.draw(renderer, draw_params_temp)

        # settings and adjustments
        plt.rc("axes", axisbelow=True)
        ax = plt.gca()
        ax.set_aspect("equal")
        ax.set_title(f"$t = {10 / 10.0:.1f}$ [s]", fontsize=28)
        ax.set_xlabel(f"$s$ [m]", fontsize=28)
        ax.set_ylabel("$d$ [m]", fontsize=28)
        plt.margins(0, 0)
        renderer.render()

        # plot reference path
        if config.debug.draw_ref_path and ref_path is not None:
            renderer.ax.plot(
                ref_path[:, 0], ref_path[:, 1], color="g", marker=".", markersize=1, zorder=19, linewidth=2.0
            )

        if config.debug.save_plots:
            save_fig(save_gif, path_output, count, verbose=(count % 5 == 0))
        else:
            plt.show()

        count += 1

    if config.debug.save_plots and save_gif:
        make_gif(path_output, "png_reach_", range(num_of_frame), str(scenario.scenario_id), duration=500)

    util_logger.print_and_log_info(logger, "\tReachable sets plotted.")
