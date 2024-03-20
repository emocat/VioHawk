"""
mutator.mutator
"""
from enum import Enum
import os

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

data_dir = os.path.join(os.path.dirname(__file__), "data")
map_dir = os.path.join(os.path.dirname(__file__), "../map/")

import abc
import copy
import random
import config
import math
import click
import json

from typing import Type, Callable

from dataparser import scenario, osm_parser

from commonroad_reach.data_structure.configuration import Configuration
from commonroad_reach.data_structure.configuration_builder import ConfigurationBuilder
from commonroad_reach.data_structure.reach.reach_interface import ReachableSetInterface
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad_reach.utility import coordinate_system as util_coordinate_system
import utils.visualization
import numpy as np

from shapely.geometry import Polygon, LineString, MultiPolygon, Point
from shapely.ops import unary_union
from utils import map_helper
from utils import helper
from utils import transform
import lgsvl


import logger

LOG = logger.get_logger(config.__prog__)


def trim_scenario_by_time_step(time_step, cr_scenario, cr_planning_problem_set, ego_states):
    # trim the scenario for each time step
    if time_step != 0:
        for ids in cr_scenario._dynamic_obstacles:
            obstacle = cr_scenario._dynamic_obstacles[ids]

            assert isinstance(obstacle._prediction, TrajectoryPrediction)
            traj = obstacle._prediction._trajectory

            # modify obstacle's initial state
            obstacle._initial_state = traj._state_list[time_step - 1]
            obstacle._initial_state.time_step = 0

            # modify obstacle's trajectory
            traj._state_list = traj._state_list[time_step:]
            for i in range(len(traj._state_list)):
                traj._state_list[i].time_step -= time_step

            # modify obstacle's occupancy set
            del obstacle.prediction._occupancy_set[:time_step]
            for i in range(len(obstacle.prediction._occupancy_set)):
                obstacle.prediction._occupancy_set[i].time_step -= time_step

        # modify the ego vehicle's initial state
        for ids in cr_planning_problem_set._planning_problem_dict:
            planning_problem = cr_planning_problem_set._planning_problem_dict[ids]
            assert isinstance(planning_problem.initial_state.position, np.ndarray)
            planning_problem.initial_state.position[0] = ego_states[time_step]["Position"]["x"]
            planning_problem.initial_state.position[1] = ego_states[time_step]["Position"]["z"]
            planning_problem.initial_state.orientation = math.radians(90 - ego_states[time_step]["Rotation"]["y"])
            planning_problem.initial_state.velocity = (
                ego_states[time_step]["Speed"] if ego_states[time_step]["Speed"] > 0 else 0
            )


def convert_polygon_to_curvilinear_coords(polygon, CLCS):
    if polygon.is_empty:
        print("polygon is empty!")
        return polygon

    try:
        if isinstance(polygon, MultiPolygon):
            print("polygon is multipolygon!")
            p = []
            for poly in polygon.geoms:
                p.append(convert_polygon_to_curvilinear_coords(poly, CLCS))
            return unary_union(p)

        x, y = polygon.exterior.coords.xy
        area = np.array(list(zip(x, y)))
        area = util_coordinate_system.convert_to_curvilinear_vertices(area, CLCS)
        area = Polygon(area)
        return area
    except Exception as e:
        LOG.error(e)
        return Polygon()


def convert_polygon_to_cartesian_coords(polygon, CLCS):
    if polygon.is_empty:
        print("polygon is empty!")
        return polygon
    try:
        if isinstance(polygon, MultiPolygon):
            print("polygon is multipolygon!")
            p = []
            for poly in polygon.geoms:
                p.append(convert_polygon_to_cartesian_coords(poly, CLCS))
            return unary_union(p)

        x, y = polygon.exterior.coords.xy
        area = np.array(list(zip(x, y)))
        area = [CLCS.convert_to_cartesian_coords(vertex[0], vertex[1]) for vertex in area]
        area = Polygon(area)
        return area
    except Exception as e:
        LOG.error(e)
        return Polygon()


def prob(num):
    if random.randint(0, 99) < num:
        return True
    else:
        return False


class MutationConfig:
    def __init__(self, _seed_scenario, _cr_config, _traces):
        self.seed_scenario: scenario.Scenario = _seed_scenario
        self.cr_config: Configuration = _cr_config
        self.traces: dict = _traces


class DrivingIntentionType(Enum):
    CROSS_INTERSECTION = 0
    LANE_CHANGE = 1
    PARKING = 2


class DrivingIntention:
    @classmethod
    def intention_cross_intersection(cls, traces, map_info, osm_map_info, config):
        junction_area = helper.get_junction_area_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], map_info, dist=100
        )
        return junction_area

    @classmethod
    def intention_lane_change(cls, traces, map_info, osm_map_info, config):
        initial_state = config.planning_problem.initial_state.position
        res = map_info.find_which_area_the_point_is_in((initial_state[0], initial_state[1]))
        assert isinstance(res, list)
        if "lane_id" not in res[0]:
            return EMPTY_POLYGON
        lane_id = res[0]["lane_id"]
        left_lane, right_lane = map_info.get_adjacent_lanes(lane_id)
        if left_lane != None:
            left_lane = Polygon(map_info.areas["lane_areas"][left_lane])
        else:
            left_lane = EMPTY_POLYGON
        if right_lane != None:
            right_lane = Polygon(map_info.areas["lane_areas"][right_lane])
        else:
            right_lane = EMPTY_POLYGON
        return left_lane.union(right_lane)

    @classmethod
    def intention_parking(cls, traces, map_info, osm_map_info, config):
        return INFINITE_POLYGON

    _intention_methods = {
        DrivingIntentionType.CROSS_INTERSECTION: intention_cross_intersection.__func__,
        DrivingIntentionType.LANE_CHANGE: intention_lane_change.__func__,
        DrivingIntentionType.PARKING: intention_parking.__func__,
    }

    @classmethod
    def resolve(cls, driving_intention, traces, map_info, osm_map_info, config):
        method = cls._intention_methods.get(driving_intention)
        if method is None:
            raise ValueError(f"Invalid driving intention: {driving_intention}")
        return method(cls, traces, map_info, osm_map_info, config)


INFINITE_POLYGON = Polygon([(-10000, 10000), (10000, 10000), (10000, -10000), (-10000, -10000)])
EMPTY_POLYGON = Polygon()


class DrivingConditionType(Enum):
    TRAFFIC_JAM = 0
    TRAFFIC_LIGHT_RED = 1
    DOUBLE_YELLOW_LINE = 2
    OVERTAKING = 3
    EGO_STOP = 4
    NPC_STOP_AT_CROSSWALK = 5
    PEDESTRIAN_AT_CROSSWALK = 6
    AT_CROSSWALK = 7
    AT_INTERSECTION = 8
    TRAFFIC_LIGHT_YELLOW = 9
    NEAR_CROSSWALK = 10
    NEAR_SIGNAL = 11
    NEAR_STOP_SIGN = 12
    PEDESTRIAN_AT_CROSSWALK_TURNING_SIDE = 13
    IN_ADJACENT_LANE = 14
    AHEAD_OF_NPC = 15


class DrivingCondition:
    flag_always_true = False

    @classmethod
    def condition_traffic_jam(cls, traces, map_info, osm_map_info, config, time_step):
        junction_area = helper.get_junction_area_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], map_info
        )

        NPCs = traces[time_step]["NPCs"]
        NPCs_in_junction_jam = []
        for NPC in NPCs:
            NPC_wheel = helper.get_four_wheel_position(NPC["Position"], NPC["Rotation"])
            NPC_polygon = Polygon(NPC_wheel)
            NPC_speed = helper.calc_speed(NPC["Velocity"])
            if NPC_polygon.distance(junction_area) == 0 and NPC_speed < 0.1:
                NPCs_in_junction_jam.append(NPC)

        print("NPCs_in_junction: ", len(NPCs_in_junction_jam))
        if len(NPCs_in_junction_jam) > 5:
            return INFINITE_POLYGON
        else:
            return EMPTY_POLYGON

    @classmethod
    def condition_traffic_light_red(cls, traces, map_info, osm_map_info, config, time_step):
        if cls.flag_always_true:
            return INFINITE_POLYGON

        traffic_lights_start = traces[time_step]["Traffic_Lights"]
        if len(traffic_lights_start) == 0 or traffic_lights_start[0]["Label"] == "red":
            return EMPTY_POLYGON

        for t in range(config.planning.steps_computation):
            traffic_lights_curr = traces[time_step + 1 + t]["Traffic_Lights"]
            traffic_lights_prev = traces[time_step + t]["Traffic_Lights"]
            if traffic_lights_prev and traffic_lights_prev[0]["Label"] == "yellow":
                if (not traffic_lights_curr) or traffic_lights_curr[0]["Label"] == "red":
                    cls.flag_always_true = True
                    return INFINITE_POLYGON

        return EMPTY_POLYGON

    @classmethod
    def condition_traffic_light_yellow(cls, traces, map_info, osm_map_info, config, time_step):
        if cls.flag_always_true:
            return INFINITE_POLYGON

        traffic_lights_start = traces[time_step]["Traffic_Lights"]
        if len(traffic_lights_start) == 0 or traffic_lights_start[0]["Label"] == "yellow":
            return EMPTY_POLYGON

        ego_states = helper.get_ego_states(traces)
        junction_area = helper.get_junction_area_ahead(
            traces[time_step]["EGO"]["Position"], traces[time_step]["EGO"]["Rotation"], map_info
        )

        for t in range(config.planning.steps_computation):
            traffic_lights_curr = traces[time_step + 1 + t]["Traffic_Lights"]
            ego_polygon = Polygon(
                helper.get_four_wheel_position(
                    ego_states[time_step + 1 + t]["Position"], ego_states[time_step + 1 + t]["Rotation"]
                )
            )

            if len(traffic_lights_curr) == 0 or traffic_lights_curr[0]["Label"] != "yellow":
                continue

            if ego_polygon.intersects(junction_area):  # if already cross the stop line at the yellow light
                return EMPTY_POLYGON
            else:
                cls.flag_always_true = True
                return INFINITE_POLYGON

        return EMPTY_POLYGON

    @classmethod
    def condition_double_yellow_line(cls, traces, map_info, osm_map_info, config, time_step):
        initial_state = config.planning_problem.initial_state.position
        res = map_info.find_which_area_the_point_is_in((initial_state[0], initial_state[1]))
        assert isinstance(res, list)
        dangerous_area = []
        if "lane_id" in res[0]:
            reverse_lanes = map_info.get_reverse_lanes(res[0]["lane_id"])
            assert isinstance(reverse_lanes, list)
            for s in reverse_lanes:
                dangerous_area.extend(map_info.areas["lane_areas"][s])
        else:
            return Polygon()
        dangerous_area = np.array(dangerous_area)
        dangerous_area = Polygon(dangerous_area)
        return dangerous_area

    @classmethod
    def condition_overtaking(cls, traces, map_info, osm_map_info, config, time_step):
        dangerous_area = []

        ego_before = traces[time_step]["EGO"]
        ego_after = traces[time_step + config.planning.steps_computation]["EGO"]
        ego_pos_curv = config.planning.CLCS.convert_to_curvilinear_coords(
            ego_before["Position"]["x"], ego_before["Position"]["z"]
        )

        area_before = map_info.check_whether_in_lane_area(
            Point(ego_before["Position"]["x"], ego_before["Position"]["z"])
        )
        area_after = map_info.check_whether_in_lane_area(Point(ego_after["Position"]["x"], ego_after["Position"]["z"]))

        lane_before = area_before[0]["lane_id"] if len(area_before) != 0 else None
        lane_after = area_after[0]["lane_id"] if len(area_after) != 0 else None

        if lane_before != lane_after and map_info.check_whether_two_lanes_are_in_the_same_road(lane_before, lane_after):
            NPCs = traces[time_step + config.planning.steps_computation]["NPCs"]
            for NPC in NPCs:
                NPC_position = Point(NPC["Position"]["x"], NPC["Position"]["z"])
                NPC_lane = map_info.check_whether_in_lane_area(NPC_position)[0]["lane_id"]
                if NPC_lane == lane_after:
                    NPC_pos_curv = config.planning.CLCS.convert_to_curvilinear_coords(NPC_position.x, NPC_position.y)

                    if abs(NPC_pos_curv[0] - ego_pos_curv[0]) < 20:
                        left_bound = map_info.areas["lane_areas_left"][lane_after]
                        left_bound = util_coordinate_system.convert_to_curvilinear_vertices(
                            left_bound, config.planning.CLCS
                        )
                        y1 = left_bound[len(left_bound) // 2][1]
                        right_bound = map_info.areas["lane_areas_right"][lane_after]
                        right_bound = util_coordinate_system.convert_to_curvilinear_vertices(
                            right_bound, config.planning.CLCS
                        )
                        y2 = right_bound[len(right_bound) // 2][1]

                        x1 = NPC_pos_curv[0]
                        x2 = NPC_pos_curv[0] + 5

                        tmp_dangerous_area = Polygon([(x1, y1), (x1, y2), (x2, y2), (x2, y1)])
                        tmp_dangerous_area = convert_polygon_to_cartesian_coords(
                            tmp_dangerous_area, config.planning.CLCS
                        )
                        dangerous_area.append(tmp_dangerous_area)

        return unary_union(dangerous_area)

    @classmethod
    def condition_ahead_of_npc(cls, traces, map_info, osm_map_info, config, time_step):
        dangerous_area = []

        ego_before = traces[time_step]["EGO"]
        ego_pos_curv = config.planning.CLCS.convert_to_curvilinear_coords(
            ego_before["Position"]["x"], ego_before["Position"]["z"]
        )

        NPCs = traces[time_step + config.planning.steps_computation]["NPCs"]
        for NPC in NPCs:
            NPC_position = Point(NPC["Position"]["x"], NPC["Position"]["z"])
            NPC_lane = map_info.check_whether_in_lane_area(NPC_position)[0]["lane_id"]
            NPC_pos_curv = config.planning.CLCS.convert_to_curvilinear_coords(NPC_position.x, NPC_position.y)

            if abs(NPC_pos_curv[0] - ego_pos_curv[0]) < 20:
                left_bound = map_info.areas["lane_areas_left"][NPC_lane]
                left_bound = util_coordinate_system.convert_to_curvilinear_vertices(left_bound, config.planning.CLCS)
                y1 = left_bound[len(left_bound) // 2][1]
                right_bound = map_info.areas["lane_areas_right"][NPC_lane]
                right_bound = util_coordinate_system.convert_to_curvilinear_vertices(right_bound, config.planning.CLCS)
                y2 = right_bound[len(right_bound) // 2][1]

                x1 = NPC_pos_curv[0]
                x2 = NPC_pos_curv[0] + 5

                tmp_dangerous_area = Polygon([(x1, y1), (x1, y2), (x2, y2), (x2, y1)])
                tmp_dangerous_area = convert_polygon_to_cartesian_coords(tmp_dangerous_area, config.planning.CLCS)
                dangerous_area.append(tmp_dangerous_area)

        return unary_union(dangerous_area)

    @classmethod
    def condition_in_adjacent_lane(cls, traces, map_info, osm_map_info, config, time_step):
        dangerous_area = []

        ego_position = traces[time_step]["EGO"]["Position"]
        ego_lane = map_info.check_whether_in_lane_area(Point(ego_position["x"], ego_position["z"]))
        if len(ego_lane) == 0:
            return EMPTY_POLYGON

        ego_lane_id = ego_lane[0]["lane_id"]
        left_lane, right_lane = map_info.get_adjacent_lanes(ego_lane_id)
        if left_lane != None:
            left_lane = Polygon(map_info.areas["lane_areas"][left_lane])
        else:
            left_lane = EMPTY_POLYGON
        if right_lane != None:
            right_lane = Polygon(map_info.areas["lane_areas"][right_lane])
        else:
            right_lane = EMPTY_POLYGON
        dangerous_area = left_lane.union(right_lane)
        return dangerous_area

    @classmethod
    def condition_npc_stop_at_crosswalk(cls, traces, map_info, osm_map_info, config, time_step):
        junction_area = helper.get_junction_area_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], map_info
        )

        NPCs = traces[time_step + config.planning.steps_computation]["NPCs"]
        for NPC in NPCs:
            NPC_wheel = helper.get_four_wheel_position(NPC["Position"], NPC["Rotation"])
            NPC_polygon = Polygon(NPC_wheel)
            NPC_speed = helper.calc_speed(NPC["Velocity"])
            if NPC_polygon.distance(junction_area) < 5 and NPC_speed < 0.1:
                return INFINITE_POLYGON

        return EMPTY_POLYGON

    @classmethod
    def condition_pedestrian_at_crosswalk(cls, traces, map_info, osm_map_info, config, time_step):
        junction_area = helper.get_junction_area_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], map_info
        )

        NPCs = traces[time_step + config.planning.steps_computation]["NPCs"]
        for NPC in NPCs:
            if NPC["Label"] == "Pedestrian":
                ped_point = Point(NPC["Position"]["x"], NPC["Position"]["z"])
                if ped_point.within(junction_area):
                    return INFINITE_POLYGON

        return EMPTY_POLYGON

    @classmethod
    def condition_ego_stop(cls, traces, map_info, osm_map_info, config, time_step):
        ego_states = helper.get_ego_states(traces)
        parking_time = 0
        for t in range(time_step, time_step + config.planning.steps_computation):
            ego_speed = ego_states[t]["Speed"]
            if abs(ego_speed) < 0.01:
                parking_time += 1
            else:
                parking_time = 0
            if parking_time > 30:
                return INFINITE_POLYGON
        return EMPTY_POLYGON

    @classmethod
    def condition_at_crosswalk(cls, traces, map_info, osm_map_info, config, time_step):
        crosswalk_area = helper.get_crosswalk_area_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], osm_map_info
        )

        return crosswalk_area

    @classmethod
    def condition_at_intersection(cls, traces, map_info, osm_map_info, config, time_step):
        junction_area = helper.get_junction_area_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], map_info
        )

        return junction_area

    @classmethod
    def condition_near_crosswalk(cls, traces, map_info, osm_map_info, config, time_step):
        crosswalk_area = helper.get_crosswalk_area_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], osm_map_info
        )

        # extend crosswalk area by 20m
        crosswalk_polygon = convert_polygon_to_curvilinear_coords(crosswalk_area, config.planning.CLCS)
        x, y = crosswalk_polygon.exterior.coords.xy
        x_mid = (max(x) + min(x)) / 2
        area = np.array(list(zip(x, y)))
        for i in range(len(area)):
            if area[i][0] < x_mid:
                area[i][0] -= 6.7056
        area = Polygon(area)
        area = convert_polygon_to_cartesian_coords(area, config.planning.CLCS)

        return area

    @classmethod
    def condition_near_signal(cls, traces, map_info, osm_map_info, config, time_step):
        traffic_light_point = helper.get_traffic_light_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], osm_map_info, 80
        )
        traffic_light_area = traffic_light_point.buffer(6.7056)

        return traffic_light_area

    @classmethod
    def condition_near_stop_sign(cls, traces, map_info, osm_map_info, config, time_step):
        stop_sign_line = helper.get_stop_sign_ahead(
            traces[0]["EGO"]["Position"], traces[0]["EGO"]["Rotation"], map_info, dist=50
        )

        x, y = stop_sign_line.coords.xy
        area1 = np.array(list(zip(x, y)))
        area = util_coordinate_system.convert_to_curvilinear_vertices(area1, config.planning.CLCS)
        for i in range(len(area)):
            area[i][0] -= 6.7056
        area2 = [config.planning.CLCS.convert_to_cartesian_coords(vertex[0], vertex[1]) for vertex in area][::-1]
        stop_line_near_area = Polygon(area1.tolist() + area2)

        return stop_line_near_area

    @classmethod
    def condition_pedestrian_at_crosswalk_turning_side(cls, traces, map_info, osm_map_info, config, time_step):
        routing = LineString(config.planning.reference_path)
        crosswalk_area = helper.get_crosswalks_to_pass(routing, osm_map_info)

        NPCs = traces[time_step + config.planning.steps_computation]["NPCs"]
        for NPC in NPCs:
            if NPC["Label"] == "Pedestrian":
                ped_point = Point(NPC["Position"]["x"], NPC["Position"]["z"])
                for crosswalk in crosswalk_area:
                    if ped_point.within(crosswalk):
                        return INFINITE_POLYGON

        return EMPTY_POLYGON

    _intention_methods = {
        DrivingConditionType.TRAFFIC_JAM: condition_traffic_jam.__func__,
        DrivingConditionType.TRAFFIC_LIGHT_RED: condition_traffic_light_red.__func__,
        DrivingConditionType.DOUBLE_YELLOW_LINE: condition_double_yellow_line.__func__,
        DrivingConditionType.OVERTAKING: condition_overtaking.__func__,
        DrivingConditionType.EGO_STOP: condition_ego_stop.__func__,
        DrivingConditionType.NPC_STOP_AT_CROSSWALK: condition_npc_stop_at_crosswalk.__func__,
        DrivingConditionType.PEDESTRIAN_AT_CROSSWALK: condition_pedestrian_at_crosswalk.__func__,
        DrivingConditionType.AT_CROSSWALK: condition_at_crosswalk.__func__,
        DrivingConditionType.AT_INTERSECTION: condition_at_intersection.__func__,
        DrivingConditionType.TRAFFIC_LIGHT_YELLOW: condition_traffic_light_yellow.__func__,
        DrivingConditionType.NEAR_CROSSWALK: condition_near_crosswalk.__func__,
        DrivingConditionType.NEAR_SIGNAL: condition_near_signal.__func__,
        DrivingConditionType.NEAR_STOP_SIGN: condition_near_stop_sign.__func__,
        DrivingConditionType.PEDESTRIAN_AT_CROSSWALK_TURNING_SIDE: condition_pedestrian_at_crosswalk_turning_side.__func__,
        DrivingConditionType.IN_ADJACENT_LANE: condition_in_adjacent_lane.__func__,
        DrivingConditionType.AHEAD_OF_NPC: condition_ahead_of_npc.__func__,
    }

    @classmethod
    def resolve(cls, driving_conditions, traces, map_info, osm_map_info, config, time_step):
        condition_areas = []
        for driving_condition in driving_conditions:
            method = cls._intention_methods.get(driving_condition)
            if method is None:
                raise ValueError(f"Invalid driving intention: {driving_condition}")
            condition_areas.append(method(cls, traces, map_info, osm_map_info, config, time_step))

        # get intersection of all the condition areas
        if len(condition_areas) == 0:
            return INFINITE_POLYGON
        result_areas = condition_areas[0]
        for area in condition_areas[1:]:
            result_areas = result_areas.intersection(area)
            if result_areas.is_empty:
                break
        return result_areas


##############################################
# Mutator
##############################################

NUM = 5


class Mutator(metaclass=abc.ABCMeta):
    def __init__(self, _config: MutationConfig) -> None:
        self.seed_scenario = None
        self.cr_config = None
        self.cr_scenario = None
        self.cr_planning_problem_set = None
        self.traces = None

        self.map_info = None

        self.reach_interface_list = None
        self.dangerous_area_list = None
        self.max_prop = -1
        self.max_timestep = -1
        self.max_t = -1
        self.max_reachable_set = None
        self.max_drivable_area = None
        self.max_dangerous_area = None
        self.max_dangerous_overlap_area = None

        self.nine_space = None
        self.nine_poly = None
        self.max_poly_i = -1

        self.driving_intention = None
        self.driving_condition = None

        self.init(_config)

    def init(self, config: MutationConfig) -> None:
        self.seed_scenario = config.seed_scenario
        self.cr_config = config.cr_config
        self.traces = config.traces
        self.map_info = map_helper.get_map_info(map_dir + "/san_francisco.json")
        self.osm_map_info = osm_parser(map_dir + "/SanFrancisco.osm")

        self.reach_interface_list = []
        self.dangerous_area_list = []

    def get_dangerous_area(self, tmp_config, time_step):
        driving_intention_area = DrivingIntention.resolve(
            self.driving_intention, self.traces, self.map_info, self.osm_map_info, tmp_config
        ).buffer(0.01)
        driving_condition_area = DrivingCondition.resolve(
            self.driving_condition, self.traces, self.map_info, self.osm_map_info, tmp_config, time_step
        ).buffer(0.01)
        dangerous_area = driving_intention_area.intersection(driving_condition_area)
        return dangerous_area

    def compute_dangerous_score(self):
        """Step 1: trim the scenario by time step, compute reachable set and dangerous area"""
        max_prop = 0
        max_timestep = 0
        max_t = 0
        max_reachable_set = Polygon()
        max_drivable_area = Polygon()
        max_dangerous_area = Polygon()
        max_dangerous_overlap_area = Polygon()
        DrivingCondition.flag_always_true = False

        assert len(self.traces) == 300, "traces is too short"

        for t in range(NUM):
            tmp_config = copy.deepcopy(self.cr_config)
            tmp_cr_scenario = copy.deepcopy(self.cr_scenario)
            tmp_cr_planning_problem_set = copy.deepcopy(self.cr_planning_problem_set)
            ego_states = helper.get_ego_states(self.traces)
            time_step = t * (200 // NUM)

            trim_scenario_by_time_step(time_step, tmp_cr_scenario, tmp_cr_planning_problem_set, ego_states)

            # compute reachable set
            tmp_config.update(scenario=tmp_cr_scenario, planning_problem_set=tmp_cr_planning_problem_set)
            tmp_config.planning.steps_computation = 200 // NUM
            reach_interface = ReachableSetInterface(tmp_config)
            reach_interface.compute_reachable_sets()

            # get drivable area
            reachable_set = reach_interface.reachable_set_at_step(tmp_config.planning.steps_computation)
            drivable_area = []
            for rs in reachable_set:
                assert rs.position_rectangle, "position_rectangle is None"
                vertice = Polygon(rs.position_rectangle.vertices)
                drivable_area.append(vertice)
            drivable_area = unary_union(drivable_area)
            drivable_area = convert_polygon_to_cartesian_coords(drivable_area, tmp_config.planning.CLCS)

            # get dangerous area
            dangerous_area = self.get_dangerous_area(tmp_config, time_step)

            ##### whether the ego is in the dangerous area #####
            ego = self.traces[time_step + tmp_config.planning.steps_computation]["EGO"]
            ego_polygon = Polygon(helper.get_four_wheel_position(ego["Position"], ego["Rotation"]))
            if ego_polygon.intersection(dangerous_area).area / ego_polygon.area > 0.1:
                LOG.info("A violation is found.")
                return -1
            ####################################################

            # calculate the proportion of drivable area in dangerous area
            dangerous_overlap_area = drivable_area.intersection(dangerous_area)
            if drivable_area.area == 0:
                prop = 0
            else:
                prop = dangerous_overlap_area.area / drivable_area.area
            print("proportion: ", prop)

            if prop > max_prop:
                max_prop = prop
                max_timestep = time_step
                max_t = t
                max_reachable_set = reachable_set
                max_drivable_area = drivable_area
                max_dangerous_area = dangerous_area
                max_dangerous_overlap_area = dangerous_overlap_area

            self.reach_interface_list.append(reach_interface)
            self.dangerous_area_list.append(dangerous_area)

        print("max proportion: ", max_prop)
        print("max t: ", max_t)
        print("max time step: ", max_timestep)
        self.max_prop = max_prop
        self.max_timestep = max_timestep
        self.max_t = max_t
        self.max_reachable_set = max_reachable_set
        self.max_drivable_area = max_drivable_area
        self.max_dangerous_area = max_dangerous_area
        self.max_dangerous_overlap_area = max_dangerous_overlap_area

        return max_prop

    def get_nine_grid(self) -> None:
        """Step 2: divide the around area into nine grids, find the grid with the largest drivable area to mutate"""
        max_config = self.reach_interface_list[self.max_t].config
        ego_position = max_config.planning_problem.initial_state.position
        ego = max_config.planning.CLCS.convert_to_curvilinear_coords(ego_position[0], ego_position[1])
        ego_area = self.map_info.check_whether_in_lane_area(Point(ego_position))

        # TODO: implement nine grid without lane borders
        # get verticle lines of the grid
        for ego_area_single in ego_area:
            if "lane_id" not in ego_area_single:
                continue
            ego_lane_id = ego_area_single["lane_id"]

            left_lane = self.map_info.areas["lane_areas_left"][ego_lane_id]
            right_lane = self.map_info.areas["lane_areas_right"][ego_lane_id]
            vertical_left_line = LineString(
                util_coordinate_system.convert_to_curvilinear_vertices(left_lane, max_config.planning.CLCS)
            )
            vertical_right_line = LineString(
                util_coordinate_system.convert_to_curvilinear_vertices(right_lane, max_config.planning.CLCS)
            )
            vertical_left_line = helper.extend_linestring_in_curvilinear(vertical_left_line, 5)
            vertical_right_line = helper.extend_linestring_in_curvilinear(vertical_right_line, 5)

            # get horizontal lines of the grid
            bound_list = []
            for road in self.map_info.Roads:
                lane_list = road["laneIdList"]
                if ego_lane_id in lane_list:
                    bound_list = []
                    for lane in lane_list:
                        left_lane = self.map_info.areas["lane_areas_left"][lane]
                        right_lane = self.map_info.areas["lane_areas_right"][lane]
                        left_bound = util_coordinate_system.convert_to_curvilinear_vertices(
                            left_lane, max_config.planning.CLCS
                        )
                        right_bound = util_coordinate_system.convert_to_curvilinear_vertices(
                            right_lane, max_config.planning.CLCS
                        )
                        if left_bound:
                            bound_list.append(left_bound[0][1])
                        if right_bound:
                            bound_list.append(right_bound[0][1])
                    break

            if bound_list:
                car_length = 2
                horizontal_up_line = LineString(
                    [[ego[0] + car_length, min(bound_list) - 3], [ego[0] + car_length, max(bound_list) + 3]]
                )
                horizontal_down_line = LineString(
                    [[ego[0] - car_length, min(bound_list) - 3], [ego[0] - car_length, max(bound_list) + 3]]
                )
                break

        lu_point = horizontal_up_line.intersection(vertical_left_line)
        ru_point = horizontal_up_line.intersection(vertical_right_line)
        ld_point = horizontal_down_line.intersection(vertical_left_line)
        rd_point = horizontal_down_line.intersection(vertical_right_line)

        left_top = max(vertical_left_line.coords[-1][0], lu_point.x + 20)
        right_top = max(vertical_right_line.coords[0][0], lu_point.x + 20)
        left_down = min(vertical_left_line.coords[0][0], ld_point.x - 20)
        right_down = min(vertical_right_line.coords[-1][0], ld_point.x - 20)

        l1 = Polygon([lu_point, (left_top, lu_point.y), (left_top, max(bound_list)), (lu_point.x, max(bound_list))])
        l2 = Polygon([lu_point, (left_top, lu_point.y), (right_top, ru_point.y), ru_point])
        l3 = Polygon([ru_point, (right_top, ru_point.y), (right_top, min(bound_list)), (ru_point.x, min(bound_list))])
        l4 = Polygon([lu_point, ld_point, (ld_point.x, max(bound_list)), (lu_point.x, max(bound_list))])
        l5 = Polygon([lu_point, ld_point, rd_point, ru_point])
        l6 = Polygon([ru_point, rd_point, (rd_point.x, min(bound_list)), (ru_point.x, min(bound_list))])
        l7 = Polygon([ld_point, (left_down, ld_point.y), (left_down, max(bound_list)), (ld_point.x, max(bound_list))])
        l8 = Polygon([ld_point, (left_down, ld_point.y), (right_down, rd_point.y), rd_point])
        l9 = Polygon([rd_point, (right_down, rd_point.y), (right_down, min(bound_list)), (rd_point.x, min(bound_list))])
        nine_l = [l1, l2, l3, l4, l5, l6, l7, l8, l9]

        for i in range(9):
            tmp_l = util_coordinate_system.convert_to_cartesian_polygons(nine_l[i], max_config.planning.CLCS, True)
            if len(tmp_l) == 1:
                nine_l[i] = tmp_l[0]._shapely_polygon
            elif len(tmp_l) > 1:
                tmp_v = [tmp_s._shapely_polygon for tmp_s in tmp_l]
                nine_l[i] = unary_union(tmp_v)
            else:
                if i < 6:
                    LOG.warning("nine_l[{}] is empty".format(i))
                nine_l[i] = Polygon()
        max_dist = 30
        left_top = max(lu_point.x + max_dist, left_top)
        right_top = max(ru_point.x + max_dist, right_top)
        left_down = min(ld_point.x - max_dist, left_down)
        right_down = min(rd_point.x - max_dist, right_down)
        space1 = Polygon([lu_point, (left_top, lu_point.y), (left_top, max(bound_list)), (lu_point.x, max(bound_list))])
        space2 = Polygon([lu_point, (left_top, lu_point.y), (right_top, ru_point.y), ru_point])
        space3 = Polygon(
            [ru_point, (right_top, ru_point.y), (right_top, min(bound_list)), (ru_point.x, min(bound_list))]
        )
        space4 = Polygon([lu_point, ld_point, (ld_point.x, max(bound_list)), (lu_point.x, max(bound_list))])
        space5 = Polygon([lu_point, ld_point, rd_point, ru_point])
        space6 = Polygon([ru_point, rd_point, (rd_point.x, min(bound_list)), (ru_point.x, min(bound_list))])
        space7 = Polygon(
            [ld_point, (left_down, ld_point.y), (left_down, max(bound_list)), (ld_point.x, max(bound_list))]
        )
        space8 = Polygon([ld_point, (left_down, ld_point.y), (right_down, rd_point.y), rd_point])
        space9 = Polygon(
            [rd_point, (right_down, rd_point.y), (right_down, min(bound_list)), (rd_point.x, min(bound_list))]
        )

        nine_space = [space1, space2, space3, space4, space5, space6, space7, space8, space9]

        for i in range(9):
            tmp_space = util_coordinate_system.convert_to_cartesian_polygons(
                nine_space[i], max_config.planning.CLCS, True
            )
            if len(tmp_space) == 1:
                nine_space[i] = tmp_space[0]._shapely_polygon
            elif len(tmp_space) > 1:
                tmp_v = [tmp_s._shapely_polygon for tmp_s in tmp_space]
                nine_space[i] = unary_union(tmp_v)
            else:
                if i < 6:
                    LOG.warning("nine_space[{}] is empty".format(i))
                nine_space[i] = Polygon()

        # draw grid line on picture
        draw_grid_line = False
        grid_line = []
        if draw_grid_line:
            for l in [vertical_left_line, vertical_right_line, horizontal_up_line, horizontal_down_line]:
                new_l = np.array(l.coords)
                try:
                    x = max_config.planning.CLCS.convert_list_of_points_to_cartesian_coords(new_l, 4)
                except Exception as e:
                    print(e)
                    exit(-1)
                grid_line.append(x)

        d_area = self.max_drivable_area.difference(self.max_dangerous_overlap_area)

        # utils.visualization.plot_polygons([self.max_drivable_area, d_area], nine_l)
        # utils.visualization.plot_scenario_with_reachable_sets(self.reach_interface_list, num_of_frame=NUM, grid_line=grid_line, danger_zone_list=self.dangerous_area_list)

        nine_poly = []
        for i in range(9):
            nine_poly.append(d_area.intersection(nine_l[i]))

        max_poly_i = -1
        for i in range(9):
            if i == 4:  # omit the center area
                continue
            print(nine_poly[i].area)
            if nine_poly[i].area > nine_poly[max_poly_i].area:
                max_poly_i = i
        print("max_poly_i: ", max_poly_i)

        self.nine_space = nine_space
        self.nine_poly = nine_poly
        self.max_poly_i = max_poly_i

    def mutate(self) -> scenario.Scenario:
        """Step 3: mutate the scenario"""
        max_config = self.reach_interface_list[self.max_t].config
        max_poly_i = self.max_poly_i
        new_scenario = copy.deepcopy(self.seed_scenario)
        new_scenario.hash = None
        new_scenario.json_obj = None

        nine_space_npc_list = [[] for i in range(9)]

        # corelate npc in trace with npc in scenario
        npc_index = dict()
        initial_npc_dict = {npc["Id"]: npc for npc in self.traces[0]["NPCs"]}
        for npc_trace in self.traces[self.max_timestep + max_config.planning.steps_computation]["NPCs"]:
            npc_id = npc_trace["Id"]
            initial_npc = initial_npc_dict.get(npc_id)

            if initial_npc is not None:
                for npc in new_scenario.elements["npc"]:
                    dx = npc.transform.position["x"] - initial_npc["Position"]["x"]
                    dz = npc.transform.position["z"] - initial_npc["Position"]["z"]
                    if dx * dx + dz * dz < 0.01:
                        npc_index[npc_trace["Id"]] = npc
                        break

        # find npc in nine space
        for npc_trace in self.traces[self.max_timestep + max_config.planning.steps_computation]["NPCs"]:
            if npc_trace["Label"] == "Pedestrian":
                continue
            wp = Point(npc_trace["Position"]["x"], npc_trace["Position"]["z"])
            for i in range(9):
                if wp.within(self.nine_space[i]):
                    nine_space_npc_list[i].append(npc_trace)

        def new_npc_overlap_with_other_elements(npc, new_position, new_rotation):
            # should not overlap with other npcs
            new_npc_polygon = Polygon(helper.get_four_wheel_position(new_position, new_rotation))
            for onpc_id, onpc in npc_index.items():
                if onpc_id == npc["Id"]:
                    continue
                onpc_polygon = Polygon(helper.get_four_wheel_position(onpc.transform.position, onpc.transform.rotation))
                if new_npc_polygon.intersects(onpc_polygon):
                    LOG.error("mutated NPC is overlap with other NPCs")
                    return True

            # should not overlap with other pedestrians
            for pedestrian in new_scenario.elements["pedestrian"]:
                pedestrian_polygon = Point(
                    pedestrian.transform.position["x"], pedestrian.transform.position["z"]
                ).buffer(1)
                if new_npc_polygon.intersects(pedestrian_polygon):
                    LOG.error("mutated NPC is overlap with pedestrians")
                    return True

            # should not overlap with ego
            ego = new_scenario.elements["ego"][0]
            ego_polygon = Polygon(helper.get_four_wheel_position(ego.transform.position, ego.transform.rotation))
            if new_npc_polygon.intersects(ego_polygon):
                LOG.error("mutated NPC is overlap with EGO")
                return True
            return False

        def npc_speed_down(npc):
            LOG.info("mutation: speed down")
            npc_scenario = npc_index[npc["Id"]]

            if npc_scenario.behaviour.name == "NPCWaypointBehaviour":
                if npc_scenario.wayPoints[self.max_timestep].speed == 0:
                    return
                for i in range(self.max_timestep, len(npc_scenario.wayPoints)):
                    t = i - self.max_timestep
                    if npc_scenario.wayPoints[i].speed - t * 0.1 < 0:
                        npc_scenario.wayPoints[i].speed = 0
                        continue
                    npc_scenario.wayPoints[i].speed -= t * 0.1
            elif npc_scenario.behaviour.name == "NPCLaneFollowBehaviour":
                if prob(50):
                    speed_to_sub = random.uniform(0, 1)
                else:
                    speed_to_sub = random.uniform(1, 5)
                npc_scenario.behaviour.maxSpeed -= speed_to_sub
                if npc_scenario.behaviour.maxSpeed < 0:
                    npc_scenario.behaviour.maxSpeed = 0
                LOG.info("mutation: speed down - {}".format(speed_to_sub))

        def npc_speed_up(npc):
            LOG.info("mutation: speed up")
            npc_scenario = npc_index[npc["Id"]]

            if npc_scenario.behaviour.name == "NPCWaypointBehaviour":
                for i in range(self.max_timestep, len(npc_scenario.wayPoints)):
                    t = i - self.max_timestep
                    npc_scenario.wayPoints[i].speed += t * 0.1
            elif npc_scenario.behaviour.name == "NPCLaneFollowBehaviour":
                if prob(50):
                    speed_to_add = random.uniform(0, 1)
                else:
                    speed_to_add = random.uniform(1, 5)
                npc_scenario.behaviour.maxSpeed += speed_to_add
                LOG.info("mutation: speed up - {}".format(speed_to_add))

        def npc_position_forward(npc):
            LOG.info("mutation: position forward")

            if prob(50):
                distance_to_add = np.array([random.uniform(0.5, 2), 0])
            elif prob(50):
                distance_to_add = np.array([random.uniform(2, 5), 0])
            else:
                distance_to_add = np.array([random.uniform(5, 10), 0])
            LOG.info("mutation: forward - {}".format(distance_to_add))

            npc_scenario: scenario.NPCVehicle = npc_index[npc["Id"]]
            old_npc_position_curv = max_config.planning.CLCS.convert_to_curvilinear_coords(
                npc_scenario.transform.position["x"], npc_scenario.transform.position["z"]
            )
            new_npc_position_curv = old_npc_position_curv + distance_to_add

            sim = lgsvl.Simulator(
                lgsvl.wise.SimulatorSettings.simulator_host, lgsvl.wise.SimulatorSettings.simulator_port
            )
            tmp_point = max_config.planning.CLCS.convert_to_cartesian_coords(
                new_npc_position_curv[0], new_npc_position_curv[1]
            )
            tmp_point_on_lane = sim.map_point_on_lane(lgsvl.Vector(tmp_point[0], 0, tmp_point[1]))
            sim.reset()
            sim.close()

            if helper.calc_distance(tmp_point_on_lane.position, tmp_point) > 3:  # cannot map point on lane
                LOG.info("cannot map point on lane, directly move forward")
                new_point_position = dict(x=tmp_point[0], y=npc_scenario.transform.position["y"], z=tmp_point[1])
                new_point_rotation = dict(x=0, y=npc_scenario.transform.rotation["y"], z=0)
            else:
                new_point_position = dict(
                    x=tmp_point_on_lane.position.x, y=tmp_point_on_lane.position.y, z=tmp_point_on_lane.position.z
                )
                new_point_rotation = dict(x=0, y=tmp_point_on_lane.rotation.y, z=0)

            if new_npc_overlap_with_other_elements(npc, new_point_position, new_point_rotation):
                return

            npc_scenario.transform = scenario.Transform(new_point_position, new_point_rotation)

        def npc_position_backward(npc):
            LOG.info("mutation: position backward")

            if prob(50):
                distance_to_sub = np.array([random.uniform(0.5, 2), 0])
            elif prob(50):
                distance_to_sub = np.array([random.uniform(2, 5), 0])
            else:
                distance_to_sub = np.array([random.uniform(5, 10), 0])
            LOG.info("mutation: backward - {}".format(distance_to_sub))

            npc_scenario: scenario.NPCVehicle = npc_index[npc["Id"]]
            old_npc_position_curv = max_config.planning.CLCS.convert_to_curvilinear_coords(
                npc_scenario.transform.position["x"], npc_scenario.transform.position["z"]
            )
            new_npc_position_curv = old_npc_position_curv - distance_to_sub

            sim = lgsvl.Simulator(
                lgsvl.wise.SimulatorSettings.simulator_host, lgsvl.wise.SimulatorSettings.simulator_port
            )
            tmp_point = max_config.planning.CLCS.convert_to_cartesian_coords(
                new_npc_position_curv[0], new_npc_position_curv[1]
            )
            tmp_point_on_lane = sim.map_point_on_lane(lgsvl.Vector(tmp_point[0], 0, tmp_point[1]))
            sim.reset()
            sim.close()

            if helper.calc_distance(tmp_point_on_lane.position, tmp_point) > 3:  # cannot map point on lane
                LOG.info("cannot map point on lane, directly move forward")
                new_point_position = dict(x=tmp_point[0], y=npc_scenario.transform.position["y"], z=tmp_point[1])
                new_point_rotation = dict(x=0, y=npc_scenario.transform.rotation["y"], z=0)
            else:
                new_point_position = dict(
                    x=tmp_point_on_lane.position.x, y=tmp_point_on_lane.position.y, z=tmp_point_on_lane.position.z
                )
                new_point_rotation = dict(x=0, y=tmp_point_on_lane.rotation.y, z=0)

            if new_npc_overlap_with_other_elements(npc, new_point_position, new_point_rotation):
                return

            npc_scenario.transform = scenario.Transform(new_point_position, new_point_rotation)

        def npc_move_forward(index, probility):
            if prob(probility):
                npc_speed_up(nine_space_npc_list[index][0])
            else:
                npc_position_forward(nine_space_npc_list[index][0])

        def npc_move_backward(index, probility):
            if prob(probility):
                npc_speed_down(nine_space_npc_list[index][0])
            else:
                npc_position_backward(nine_space_npc_list[index][0])

        def new_npc(area=None):
            LOG.info("mutation: add new npc")

            center = area.centroid
            sim = lgsvl.Simulator(
                lgsvl.wise.SimulatorSettings.simulator_host, lgsvl.wise.SimulatorSettings.simulator_port
            )
            tmp_point = sim.map_point_on_lane(lgsvl.Vector(center.x, 0, center.y))
            sim.reset()
            sim.close()

            if new_npc_overlap_with_other_elements(dict(Id=-1), tmp_point.position, tmp_point.rotation):
                return

            new_npc = scenario.NPCVehicle()
            new_npc.uid = ""
            new_npc.variant = "SUV"  # TODO
            new_npc.parameterType = ""
            new_npc.color = dict(r=0, g=0, b=0)
            new_npc.wayPoints = []
            new_npc.behaviour = scenario.NPCBehaviour()
            new_npc.behaviour.name = "NPCLaneFollowBehaviour"
            new_npc.behaviour.maxSpeed = 0
            new_npc.behaviour.isLaneChange = True  # random.choice([True, False])
            new_npc.transform = scenario.Transform(
                dict(x=tmp_point.position.x, y=tmp_point.position.y, z=tmp_point.position.z),
                dict(x=0, y=tmp_point.rotation.y, z=0),
            )
            new_scenario.elements["npc"].append(new_npc)

        def npc_in_dangerous_area(npc):
            wp = np.array([npc["Position"]["x"], npc["Position"]["z"]])
            wp = Point(wp)
            return wp.within(self.max_dangerous_area)

        if max_poly_i != -1:
            if (
                self.max_dangerous_area.intersection(self.nine_space[max_poly_i]).area
                / self.nine_space[max_poly_i].area
                < 0.05
            ):
                danger_in_poly = False
            else:
                danger_in_poly = self.max_dangerous_area.intersection(self.nine_space[max_poly_i]).area > 0
        else:
            danger_in_poly = False

        if max_poly_i == 1:
            if nine_space_npc_list[max_poly_i]:
                if danger_in_poly:  # if dangerous area exists in the grid
                    npc_move_forward(max_poly_i, 50)
                else:
                    npc_move_backward(max_poly_i, 50)
            else:
                if not danger_in_poly:
                    new_npc(self.nine_poly[max_poly_i])
        elif max_poly_i == 0 or max_poly_i == 2:
            if prob(30):
                new_npc(self.nine_poly[max_poly_i])
            elif nine_space_npc_list[max_poly_i]:
                npc_move_backward(max_poly_i, 50)
            elif nine_space_npc_list[max_poly_i + 3]:
                npc_move_forward(max_poly_i + 3, 50)
            elif nine_space_npc_list[max_poly_i + 6]:
                npc_move_forward(max_poly_i + 6, 50)
            else:
                new_npc(self.nine_poly[max_poly_i])
        elif max_poly_i == 3 or max_poly_i == 5:
            if prob(30):
                new_npc(self.nine_poly[max_poly_i])
            elif nine_space_npc_list[max_poly_i]:
                LOG.error("mutation strategy for poly {} is not implemented yet!".format(max_poly_i))
            elif nine_space_npc_list[max_poly_i - 3]:
                npc_move_backward(max_poly_i - 3, 50)
            elif nine_space_npc_list[max_poly_i + 3]:
                npc_move_forward(max_poly_i + 3, 50)
            else:
                new_npc(self.nine_poly[max_poly_i])
        elif max_poly_i == -1:
            if nine_space_npc_list[1]:
                npc_move_forward(1, 0)
        else:
            LOG.error("mutation strategy for poly {} is not implemented yet!".format(max_poly_i))

        return new_scenario

    def mutation(self) -> scenario.Scenario:
        self.get_nine_grid()
        return self.mutate()


class MutatorFactory:
    """The factory class for creating different mutators"""

    registry = {}

    @classmethod
    def register(cls, name: str) -> Callable[[Type[Mutator]], None]:
        def inner_wrapper(wrapper_class: Type[Mutator]) -> None:
            cls.registry[name] = wrapper_class

        return inner_wrapper

    @classmethod
    def create_mutator(cls, name: str, **kwargs) -> "Mutator":
        exec_class = cls.registry[name]
        mutator = exec_class(kwargs["config"])
        return mutator


@MutatorFactory.register("traffic_light_red")
class RedLightMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.CROSS_INTERSECTION
        self.driving_condition = [DrivingConditionType.TRAFFIC_LIGHT_RED]


@MutatorFactory.register("double_yellow_line")
class DoubleYellowLineMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.LANE_CHANGE
        self.driving_condition = [DrivingConditionType.DOUBLE_YELLOW_LINE]


@MutatorFactory.register("traffic_jam")
class TrafficJamMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.CROSS_INTERSECTION
        self.driving_condition = [DrivingConditionType.TRAFFIC_JAM]


@MutatorFactory.register("overtaking")
class OvertakingMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.LANE_CHANGE
        self.driving_condition = [DrivingConditionType.AHEAD_OF_NPC, DrivingConditionType.IN_ADJACENT_LANE]


@MutatorFactory.register("car_stop_at_crosswalk")
class CarStopAtCrosswalkMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.CROSS_INTERSECTION
        self.driving_condition = [DrivingConditionType.AT_CROSSWALK, DrivingConditionType.NPC_STOP_AT_CROSSWALK]


@MutatorFactory.register("pedestrian_at_crosswalk")
class PedestrianAtCrosswalkMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.CROSS_INTERSECTION
        self.driving_condition = [DrivingConditionType.AT_CROSSWALK, DrivingConditionType.PEDESTRIAN_AT_CROSSWALK]


@MutatorFactory.register("park_at_crosswalk")
class ParkAtCrosswalkMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.PARKING
        self.driving_condition = [DrivingConditionType.AT_CROSSWALK, DrivingConditionType.EGO_STOP]


@MutatorFactory.register("park_at_intersection")
class ParkAtIntersectionMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.PARKING
        self.driving_condition = [DrivingConditionType.AT_INTERSECTION, DrivingConditionType.EGO_STOP]


@MutatorFactory.register("traffic_light_yellow")
class YellowLightMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.CROSS_INTERSECTION
        self.driving_condition = [DrivingConditionType.TRAFFIC_LIGHT_YELLOW]


@MutatorFactory.register("park_near_crosswalk")
class ParkNearCrosswalkMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.PARKING
        self.driving_condition = [DrivingConditionType.NEAR_CROSSWALK, DrivingConditionType.EGO_STOP]


@MutatorFactory.register("park_near_signal")
class ParkNearSignalMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.PARKING
        self.driving_condition = [DrivingConditionType.NEAR_SIGNAL, DrivingConditionType.EGO_STOP]


@MutatorFactory.register("park_near_stop_sign")
class ParkNearStopSignMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.PARKING
        self.driving_condition = [DrivingConditionType.NEAR_STOP_SIGN, DrivingConditionType.EGO_STOP]


@MutatorFactory.register("pedestrian_at_crosswalk_turning_side")
class PedestrianAtCrosswalkTurningSideMutator(Mutator):
    def __init__(self, _config: MutationConfig):
        super().__init__(_config)
        self.driving_intention = DrivingIntentionType.CROSS_INTERSECTION
        self.driving_condition = [
            DrivingConditionType.PEDESTRIAN_AT_CROSSWALK_TURNING_SIDE,
            DrivingConditionType.AT_INTERSECTION,
        ]


def create_mutator(seed_scenario: scenario.Scenario, trace: str, map: str, rule: str):
    with open(trace, "r") as f:
        seed_trace = json.load(f)
    initial_config = ConfigurationBuilder(path_root=data_dir).build_configuration("mutation")

    config = MutationConfig(seed_scenario, initial_config, seed_trace)
    mutator = MutatorFactory.create_mutator(rule, config=config)

    cr_scenario, cr_planning_problem_set = transform.generate_commonroad_scenario(
        "mutation", trace, map, seed_scenario.seed_path
    )
    mutator.cr_scenario = cr_scenario
    mutator.cr_planning_problem_set = cr_planning_problem_set

    return mutator


@click.command()
@click.option(
    "-s", "--seed", type=click.Path(exists=True, dir_okay=False), required=True, help="scenario seed file to be mutated"
)
@click.option(
    "-t", "--trace", type=click.Path(exists=True, dir_okay=False), required=True, help="trace file of the seed"
)
@click.option(
    "-m",
    "--map",
    type=click.Path(dir_okay=False, exists=True),
    required=True,
    help="The file which contains the map info.",
)
@click.option("-r", "--rule", type=str, required=True, help="targeted traffic rule")
@click.option(
    "-o", "--output", type=click.Path(exists=False, dir_okay=False), required=True, help="output path for mutated seed"
)
def cli(seed: str, trace: str, map: str, rule: str, output: str):
    seed_scenario = scenario.Scenario(seed)

    mutator = create_mutator(seed_scenario, trace, map, rule)

    mutator.compute_dangerous_score()
    new_scenario = mutator.mutation()
    new_scenario.store(output)


if __name__ == "__main__":
    cli()
