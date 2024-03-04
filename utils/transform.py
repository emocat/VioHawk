from commonroad.planning.planning_problem import PlanningProblemSet, PlanningProblem
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.scenario import Tag, ScenarioID
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.geometry.shape import Rectangle
from commonroad.scenario.trajectory import State, Trajectory
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.planning.goal import GoalRegion
from commonroad.common.util import Interval
from pyproj import Proj
import json
import math
import sys, os
import numpy as np
import click

sys.path.append(os.path.join(os.path.dirname(__file__)))

from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

time_duration = 300  # 60


LGSVL_Obstacle_To_CR_Obstacle = {
    "Sedan": "car",
    "BoxTruck": "truck",
    "SchoolBus": "bus",
    "Bicyclist": "bicycle",
    "Robin": "pedestrian",
    "Pedestrian": "pedestrian",
    "taxi": "Hatchback",
    "Hatchback": "taxi",
    "SUV": "car",
    "Jeep": "car",
}


obstacle_class_dict = {
    "truck": ObstacleType.TRUCK,
    "car": ObstacleType.CAR,
    "bus": ObstacleType.BUS,
    "bicycle": ObstacleType.BICYCLE,
    "pedestrian": ObstacleType.PEDESTRIAN,
    "taxi": ObstacleType.TAXI,
}


def get_trajectories(data_path):
    with open(data_path, "r") as f:
        traces = json.load(f)

    npc_state_list = []
    ego_states = []
    npc_dict = {}

    for trace in traces:
        ego_trace = trace["EGO"]
        ego_wp = dict(
            Id=ego_trace["Id"],
            Label="Ego",
            Position=ego_trace["Position"],
            Rotation=ego_trace["Rotation"],
            Speed=ego_trace["LinearVelocity"]["x"],
            Scale=ego_trace["Scale"],
        )
        ego_states.append(ego_wp)

        if trace["NPCs"]:
            for npc in trace["NPCs"]:
                npc_wp = dict(
                    Id=npc["Id"],
                    Label=npc["Label"],
                    Position=npc["Position"],
                    Rotation=npc["Rotation"],
                    Speed=npc["LinearVelocity"]["x"],
                    Scale=npc["Scale"],
                )

                if npc["Id"] in npc_dict:
                    npc_dict[npc["Id"]].append(npc_wp)
                else:
                    npc_dict[npc["Id"]] = [npc_wp]

    ego_states = ego_states[-time_duration:]
    npc_state_list = []
    for npc_id in npc_dict:
        npc_state_list.append(npc_dict[npc_id][-time_duration:])
    return ego_states, npc_state_list


def get_destination(seed_path):
    lgsvl_dst = dict(position=dict(x=0, y=0, z=0), rotation=dict(x=0, y=0, z=0))
    with open(seed_path, "r") as f:
        json_object = json.load(f)
        for agent in json_object["agents"]:
            if agent["type"] != 1:
                continue
            if "destinationPoint" in agent:
                lgsvl_dst = agent["destinationPoint"]
    return lgsvl_dst


def output_xml(scenario, planning_problem_set, output_path):
    writer = CommonRoadFileWriter(
        scenario=scenario,
        planning_problem_set=planning_problem_set,
        author="viohawk",
        affiliation="",
        source="",
        tags={Tag.URBAN},
    )
    writer.write_to_file(output_path, OverwriteExistingFile.ALWAYS)


def generate_init_scanerio_with_map(xodr_path):
    from pathlib import Path

    xodr_path = Path(xodr_path)
    scenario = opendrive_to_commonroad(xodr_path)
    return scenario


def get_georeference(xodr_path):
    f = open(xodr_path, "r")
    map_content = f.read()
    origin_geo_reference = map_content[
        map_content.find("<geoReference> ") + len("<geoReference> ") : map_content.find(" </geoReference>")
    ]
    arrays = origin_geo_reference.split(" ")
    arrays[4] = "+x_0=0"
    arrays[5] = "+y_0=0"
    return " ".join(arrays)


def cr2lgsvl_position(_cr_position_x, _cr_position_y, geo_reference):
    a = Proj("+proj=utm +zone=32 +ellps=WGS84")
    lon, lat = a(_cr_position_x, _cr_position_y, inverse=True)
    b = Proj(geo_reference)
    p_x, p_y = b(lon, lat)
    p_z = 0
    lgsvl_position = {}
    lgsvl_position["x"] = p_x
    lgsvl_position["y"] = p_z
    lgsvl_position["z"] = p_y
    return lgsvl_position


def lgsvl2cr_position(x, y, geo_reference):
    a = Proj(geo_reference)
    lon, lat = a(x, y, inverse=True)
    b = Proj("+proj=utm +zone=32 +ellps=WGS84")
    p_x, p_y = b(lon, lat)
    return p_x, p_y


def cr2lgsvl_rotation(_cr_orientation):
    lgsvl_rotation = {}
    lgsvl_rotation["x"] = 0
    lgsvl_rotation["y"] = 90 - math.degrees(_cr_orientation)
    lgsvl_rotation["z"] = 0
    return lgsvl_rotation


def lgsvl2cr_rotation(lgsvl_rotation):
    _cr_orientation = math.radians(90 - lgsvl_rotation)
    return _cr_orientation


def generate_obstacles(scenario, npc_state_list, geo_reference, convert_to_cr=True):
    dynamic_obstacles = []
    for npc_state in npc_state_list:
        if len(npc_state) > 0:
            dynamic_obstacle = generate_single_dynamic_obstacle(scenario, npc_state, geo_reference, convert_to_cr)
            dynamic_obstacles.append(dynamic_obstacle)

    return dynamic_obstacles


def generate_single_dynamic_obstacle(scenario, npc_state, geo_reference, convert_to_cr):
    dynamic_obstacle_id = scenario.generate_object_id()
    lgsvl_type = npc_state[0]["Label"]
    npc_scale = npc_state[0]["Scale"]
    dynamic_obstacle_type = obstacle_class_dict[LGSVL_Obstacle_To_CR_Obstacle[lgsvl_type]]
    dynamic_obstacle_shape = Rectangle(width=npc_scale["x"], length=npc_scale["z"])
    dynamic_obstacle_initial_state = None
    state_list = []

    for i in range(time_duration):
        if i < len(npc_state):
            state = npc_state[i]
        else:
            state = npc_state[-1]
        if convert_to_cr:
            x, y = lgsvl2cr_position(state["Position"]["x"], state["Position"]["z"], geo_reference)
        else:
            x, y = state["Position"]["x"], state["Position"]["z"]
        v = state["Speed"]
        theta = lgsvl2cr_rotation(state["Rotation"]["y"])
        if i < len(npc_state) - 1:
            a = (npc_state[i + 1]["Speed"] - v) / 0.1
        else:
            a = 0
        cr_state = State()
        cr_state.position = np.array([x, y])
        cr_state.velocity = v
        cr_state.orientation = theta
        cr_state.acceleration = a
        cr_state.time_step = i
        state_list.append(cr_state)
    dynamic_obstacle_initial_state = state_list[0]

    dynamic_obstacle_trajectory = Trajectory(1, state_list[1:])
    dynamic_obstacle_prediction = TrajectoryPrediction(dynamic_obstacle_trajectory, dynamic_obstacle_shape)

    return DynamicObstacle(
        dynamic_obstacle_id,
        dynamic_obstacle_type,
        dynamic_obstacle_shape,
        dynamic_obstacle_initial_state,
        dynamic_obstacle_prediction,
    )


def generate_planning_problem(scenario, ego_state, cr_dst_pos, cr_dst_orientation, geo_reference, convert_to_cr=True):
    planning_problem_id = scenario.generate_object_id()
    state = ego_state[0]
    scale = ego_state[0]["Scale"]
    if convert_to_cr:
        x, y = lgsvl2cr_position(state["Position"]["x"], state["Position"]["z"], geo_reference)
    else:
        x, y = state["Position"]["x"], state["Position"]["z"]
    v = state["Speed"]
    theta = lgsvl2cr_rotation(state["Rotation"]["y"])
    dynamic_obstacle_initial_state = State()
    dynamic_obstacle_initial_state.position = np.array([x, y])
    dynamic_obstacle_initial_state.velocity = v
    dynamic_obstacle_initial_state.orientation = theta
    dynamic_obstacle_initial_state.time_step = 0
    dynamic_obstacle_initial_state.yaw_rate = 0.0
    dynamic_obstacle_initial_state.slip_angle = 0.0

    goal_position = Rectangle(
        width=scale["x"], length=scale["z"], center=np.array(cr_dst_pos), orientation=cr_dst_orientation
    )
    dynamic_obstacle_final_state = State()
    time_step_half_range = 25
    time_step_interval = Interval(0, time_duration + time_step_half_range)
    dynamic_obstacle_final_state.position = goal_position
    dynamic_obstacle_final_state.time_step = time_step_interval
    goal_region = GoalRegion([dynamic_obstacle_final_state])
    return PlanningProblem(planning_problem_id, dynamic_obstacle_initial_state, goal_region)


def generate_commonroad_scenario(scenario_name, data_path, xodr_path, seed_path):
    lgsvl_dst = get_destination(seed_path)
    scenario = generate_init_scanerio_with_map(xodr_path)
    scenario.scenario_id = ScenarioID.from_benchmark_id(scenario_name, "2020a")
    ego_state, npc_state_list = get_trajectories(data_path)
    geo_reference = get_georeference(xodr_path)

    cr_dst_pos = (lgsvl_dst["position"]["x"], lgsvl_dst["position"]["z"])
    cr_dst_orientation = lgsvl2cr_rotation(lgsvl_dst["rotation"]["y"])

    dynamic_obstacles = generate_obstacles(scenario, npc_state_list, geo_reference, convert_to_cr=False)
    for do in dynamic_obstacles:
        scenario.add_objects(do)

    planning_problem_set = PlanningProblemSet()
    planning_problem = generate_planning_problem(
        scenario, ego_state, cr_dst_pos, cr_dst_orientation, geo_reference, convert_to_cr=False
    )
    planning_problem_set.add_planning_problem(planning_problem)

    return scenario, planning_problem_set


@click.command()
@click.option("--scenario_name", type=str, required=True, nargs=1)
@click.option("--trace_path", type=click.Path(dir_okay=False, exists=True), required=True, nargs=1)
@click.option("--xodr_path", type=click.Path(dir_okay=False, exists=True), required=True, nargs=1)
@click.option("--seed", type=click.Path(dir_okay=False, exists=True), required=True, nargs=1)
@click.option("--output", type=click.Path(dir_okay=False, exists=False), required=True, nargs=1)
def convert_trace_to_commonroad(scenario_name, trace_path, xodr_path, seed, output):
    scenario, planning_problem_set = generate_commonroad_scenario(scenario_name, trace_path, xodr_path, seed)
    output_xml(scenario, planning_problem_set, output)


if __name__ == "__main__":
    convert_trace_to_commonroad()
