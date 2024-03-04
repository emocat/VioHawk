import os, sys
from .map.Object import Opendrive2Apollo

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import copy
import math
import random
from datetime import datetime
import hashlib

from dataparser import scenario
from dataparser.scenario import NPCVehicle, Pedestrian, StaticObstacle
from utils import helper

import config as _Config
import logger as _Logger

LOG = _Logger.get_logger(_Config.__prog__)


class DriveFuzzFactory:
    def __init__(self, seed_scenario: scenario.Scenario, trace: str, rule: str) -> None:
        self.scenario = seed_scenario
        self.trace = helper.get_trace(trace)
        self.trace_add_accelaration()

        self.mutation_choice = dict()
        self.init_mutation_config()

        self.opendrive2apollo = Opendrive2Apollo(os.path.dirname(os.path.abspath(__file__)) + "/map/map_files/SanFrancisco.xodr")

    def trace_add_accelaration(self):
        for t in range(len(self.trace) - 1):
            v1 = self.trace[t]["EGO"]["Velocity"]
            v2 = self.trace[t + 1]["EGO"]["Velocity"]
            self.trace[t]["EGO"]["Acceleration"]["x"] = v2["x"] - v1["x"]
            self.trace[t]["EGO"]["Acceleration"]["y"] = v2["y"] - v1["y"]
            self.trace[t]["EGO"]["Acceleration"]["z"] = v2["z"] - v1["z"]

    def init_mutation_config(self):
        self.mutation_choice["environments"] = {"weather": True, "time": True, "road": True}
        self.mutation_choice["ego"] = False
        self.mutation_choice["pedestrian"] = {"change_num": True, "variant": True, "speed": True, "cross": True, "range": (0, 30)}
        self.mutation_choice["roadblock"] = {"change_num": True, "range": (0, 30)}
        self.mutation_choice["motor_vehicles"] = {"change_num": True, "variant": True, "speed": True, "range": (0, 30)}
        self.mutation_choice["bicycles"] = {"change_num": True, "speed": True, "range": (0, 30)}

    def closest_npc(self):
        criticalDist = 10
        minDist = criticalDist

        for trace in self.trace:
            ego_position = trace["EGO"]["Position"]
            for npc in trace["NPCs"]:
                npc_position = npc["Position"]
                curD = helper.calc_distance(ego_position, npc_position)
                if minDist > curD:
                    minDist = curD
                    closest_npc = npc

        Score = 40 / math.pow(minDist + 0.1, 2)
        return Score

    def ego_reaction(self):
        ha = 0  # hard accelerate count
        hb = 0  # hard break count
        ht = 0  # hard turn count
        g = 9.8  # gravitational acceleration

        for trace in self.trace:
            ego = trace["EGO"]
            vlinx = ego["Velocity"]["x"]
            vliny = ego["Velocity"]["y"]
            vlinz = ego["Velocity"]["z"]
            ax = ego["Acceleration"]["x"]
            ay = ego["Acceleration"]["y"]
            az = ego["Acceleration"]["z"]
            # for ha and hb
            sgn = 1 if (vlinx * ax + vliny * ay + vlinz * az) >= 0 else -1
            a = math.sqrt(ax**2 + az**2)
            kab = sgn * a / g
            if kab >= 0.03:
                ha += 1
            elif kab <= -0.03:
                hb += 1

        return ha + hb

    def calc_feedback(self):
        return -(self.closest_npc() + self.ego_reaction())

    def mutation(self):
        # TODO mutate the initial scenario to generate xx new scenarios
        _scenario = self.scenario
        mutation_choice = self.mutation_choice
        _rand = 1
        opendrive2apollo = self.opendrive2apollo

        new_scenarios = []

        # mutate
        for _ in range(0, _rand):
            scenario = copy.deepcopy(_scenario)
            scenario.hash = None
            scenario.json_obj = None

            path = []
            NPC_first_position = []
            pedestrian_first_position = []
            road_block_position = []

            pedestrian_num = 0
            motor_vehicles_num = 0
            bicycles_num = 0
            road_block = 0
            is_pedestrian_variant = False
            is_pedestrian_speed = False
            is_motor_vehicles_variant = False
            is_motor_vehicles_speed = False
            # for element in scenario.elements:
            #     if element.name == "weather":
            for element in scenario.elements["weather"]:
                if mutation_choice["environments"]["weather"]:
                    element = mut_weather(element)
                    LOG.info("mutate weather")
                if mutation_choice["environments"]["road"]:
                    element = mut_road_damage(element)
                    LOG.info("mutate road damage")

            for element in scenario.elements["time"]:
                if mutation_choice["environments"]["time"]:
                    element = mut_time(element)
                    LOG.info("mutate time")
            
            for element in scenario.elements["pedestrian"]:
                pedestrian_first_position.append((element.transform.position["x"], element.transform.position["z"]))
                pedestrian_num += 1
                rand_num = 2
                if mutation_choice["pedestrian"]["variant"]:
                    tmp = random.randint(1, rand_num)
                    if tmp == 1:
                        element = mut_ped_variant(element)
                    is_pedestrian_variant = True
                if mutation_choice["pedestrian"]["speed"]:
                    rand_num = 2
                    tmp = random.randint(1, rand_num)
                    if tmp == 1:
                        element.wayPoints = mut_waypoint_speed(element.wayPoints, 1, 3)
                        is_pedestrian_speed = True

            for element in scenario.elements["npc"]:
                NPC_first_position.append((element.transform.position["x"], element.transform.position["z"]))
                rand_num = 2
                if element.variant != "Bicyclist":
                    motor_vehicles_num += 1
                    if mutation_choice["motor_vehicles"]["variant"]:
                        tmp = random.randint(1, rand_num)
                        if tmp == 1:
                            element = mut_npc_variant(element)
                            is_motor_vehicles_variant = True
                        tmp = random.randint(1, rand_num)
                        if tmp == 1:
                            element = mut_color(element)

                    if mutation_choice["motor_vehicles"]["speed"]:
                        tmp = random.randint(1, rand_num)
                        if tmp == 1:
                            element.wayPoints = mut_waypoint_speed(element.wayPoints, 6, 10)
                            is_motor_vehicles_speed = True

                else:
                    bicycles_num += 1
                    if mutation_choice["bicycles"]["speed"]:
                        element.wayPoints = mut_waypoint_speed(element.wayPoints, 4, 7)
                LOG.info("change npc")

            for element in scenario.elements["obstacle"]:
                road_block += 1
                road_block_position.append((element.transform.position["x"], element.transform.position["z"]))

            for element in scenario.elements["ego"]:
                if mutation_choice["ego"]:
                    element = change_destination(opendrive2apollo, element)
                    LOG.info("mutate the destination of ego")
                _, beg_road_id, beg_lane_id = opendrive2apollo.get_road_and_lane_id((element.transform.position["x"], element.transform.position["z"]))
                begPosition = (element.transform.position["x"], element.transform.position["z"])
            if is_pedestrian_variant:
                LOG.info("mutate the pedsrtian variant")
            if is_pedestrian_speed:
                LOG.info("mutate the pedsrtian speed")
            if is_motor_vehicles_variant:
                LOG.info("mutate the vehicles variant")
            if is_motor_vehicles_speed:
                LOG.info("mutate the vehicles speed")
            if mutation_choice["motor_vehicles"]["change_num"] and motor_vehicles_num < mutation_choice["motor_vehicles"]["range"][1]:
                LOG.info("add motor vehicle")
                new1 = add_waypoint_npc(opendrive2apollo, NPC_first_position, road_block_position, (beg_road_id, beg_lane_id, begPosition), False)
                if new1 != None:
                    motor_vehicles_num += 1
                    # scenario.elements.append(new1)
                    scenario.elements["npc"].append(new1)
                    NPC_first_position.append((new1.transform.position["x"], new1.transform.position["z"]))
                new1 = add_immobile_npc(opendrive2apollo, NPC_first_position, road_block_position, (beg_road_id, beg_lane_id, begPosition), False)
                if new1 != None:
                    motor_vehicles_num += 1
                    # scenario.elements.append(new1)
                    scenario.elements["npc"].append(new1)
                    NPC_first_position.append((new1.transform.position["x"], new1.transform.position["z"]))

                new1 = add_lane_follow_npc(opendrive2apollo, NPC_first_position, road_block_position, (beg_road_id, beg_lane_id, begPosition), False)
                if new1 != None:
                    motor_vehicles_num += 1
                    # scenario.elements.append(new1)
                    scenario.elements["npc"].append(new1)
                    NPC_first_position.append((new1.transform.position["x"], new1.transform.position["z"]))

            if mutation_choice["bicycles"]["change_num"] and bicycles_num < mutation_choice["bicycles"]["range"][1]:
                LOG.info("add bicycles")
                new1 = add_waypoint_npc(opendrive2apollo, NPC_first_position, road_block_position, (beg_road_id, beg_lane_id, begPosition), True)
                if new1 != None:
                    bicycles_num += 1
                    # scenario.elements.append(new1)
                    scenario.elements["npc"].append(new1)
                    NPC_first_position.append((new1.transform.position["x"], new1.transform.position["z"]))

                new1 = add_immobile_npc(opendrive2apollo, NPC_first_position, road_block_position, (beg_road_id, beg_lane_id, begPosition), True)
                if new1 != None:
                    motor_vehicles_num += 1
                    # scenario.elements.append(new1)
                    scenario.elements["npc"].append(new1)
                    NPC_first_position.append((new1.transform.position["x"], new1.transform.position["z"]))

                new1 = add_lane_follow_npc(opendrive2apollo, NPC_first_position, road_block_position, (beg_road_id, beg_lane_id, begPosition), True)
                if new1 != None:
                    bicycles_num += 1
                    # scenario.elements.append(new1)
                    scenario.elements["npc"].append(new1)
                    NPC_first_position.append((new1.transform.position["x"], new1.transform.position["z"]))

            if mutation_choice["pedestrian"]["change_num"] and pedestrian_num < mutation_choice["pedestrian"]["range"][1]:
                LOG.info("add pedestrian")
                tmp = 0
                if mutation_choice["pedestrian"]["cross"]:
                    tmp = 1
                is_cross = random.randint(0, tmp)
                if is_cross:
                    new1 = add_cross_road_pedestrian(opendrive2apollo, pedestrian_first_position, (beg_road_id, beg_lane_id, begPosition), path)
                else:
                    new1 = add_walk_randomly_pedestrian(opendrive2apollo, pedestrian_first_position, (beg_road_id, beg_lane_id, begPosition))
                if new1 != None:
                    pedestrian_num += 1
                    # scenario.elements.append(new1)
                    scenario.elements["pedestrian"].append(new1)
                    pedestrian_first_position.append((new1.transform.position["x"], new1.transform.position["z"]))

            new_scenarios.append(scenario)

        return new_scenarios[0]


def mut_weather(weather):
    weather.rain = random.uniform(0, 1)
    weather.fog = random.uniform(0, 1)
    weather.wetness = random.uniform(0, 1)
    weather.cloudiness = random.uniform(0, 1)

    LOG.info("change the weather to rain:{}, fog:{}, wetness:{},cloudiness:{}.".format(weather.rain, weather.fog, weather.wetness, weather.cloudiness))
    return weather


def mut_road_damage(road):
    cur = road.damage
    road.damage = random.uniform(0, 1)
    LOG.info("change the road damage from {} to {}".format(cur, road.damage))
    return road


def mut_time(time):
    def which_day(year, month):
        if month == 2:
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return random.randint(1, 29)
            else:
                return random.randint(1, 28)
        elif month in (1, 3, 5, 7, 8, 10, 12):
            return random.randint(1, 31)
        else:
            return random.randint(1, 30)

    year = random.randint(2000, 2023)
    month = random.randint(1, 12)
    day = which_day(year, month)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    time2 = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    time.dt = time2
    return time


def mut_light_policy(light, begin, end):
    policy = light.policy
    if len(policy) == 0:
        return light
    for action in policy:
        if action["action"] == "wait":
            action["value"] = random.randint(begin, end)
    light.policy = policy
    return light


def mut_waypoint_speed(waypoints, begin, end):
    speed = random.randint(begin, end)
    if len(waypoints) == 0:
        return waypoints
    for waypoint in waypoints:
        waypoint.speed = speed
    return waypoints


def mut_waypoint_waittime(waypoints, begin, end):
    if len(waypoints) == 0:
        return waypoints
    for waypoint in waypoints:
        waypoint.waitTime = random.randint(begin, end)
    return waypoints


def mut_color(NPC):
    NPC.color["r"] = random.uniform(0, 1)
    NPC.color["g"] = random.uniform(0, 1)
    NPC.color["b"] = random.uniform(0, 1)
    return NPC


def mut_npc_variant(npc):
    npc_name = ["SUV", "Jeep", "Hatchback", "SchoolBus", "BoxTruck"]
    # npc_name = ["SchoolBus", "BoxTruck"]
    npc.variant = npc_name[random.randint(0, len(npc_name) - 1)]
    npc.agent_name = npc.variant
    return npc


def mut_ped_variant(ped):
    ped_name = ["Bob", "EntrepreneurFemale", "Howard", "Johny", "Pamela", "Presley", "Robin", "Stephen", "Zoe", "Deer", "Turkey", "Bill"]
    ped.variant = ped_name[random.randint(0, len(ped_name) - 1)]
    ped.agent_name = ped.variant
    return ped


def add_npc_follow_lane(road_id_1, opendrive2apollo, ego_position, npc_position, road_block_position, is_bicycle):
    beg_road_id, beg_lane_id, begPosition = ego_position
    count = 0
    while True:
        s, rotation, mid_point, road_id, lane_id = opendrive2apollo.get_ran_road_point(int(road_id_1), "driving")
        if s == None:
            LOG.warning("Wrong road id {}".format(road_id_1))
            return None
        count += 1
        if count > 30:
            LOG.warning("Can't find a position to seat the NPC")
            return None
        # if int(beg_road_id) == int(road_id) and int(beg_lane_id) == int(lane_id):
        if math.sqrt((begPosition[0] - mid_point[0]) ** 2 + (begPosition[1] - mid_point[1]) ** 2) < 10:
            if not (int(beg_road_id) == int(road_id) and int(beg_lane_id) != int(lane_id)):
                continue
        is_npc_collision = False
        for position in npc_position:
            is_in, npc_road_id, npc_lane_id = opendrive2apollo.get_road_and_lane_id(position)
            if not is_in:
                continue
            if npc_road_id == None or road_id == None or npc_lane_id == None or lane_id == None:
                LOG.error("!!!!!!!!!!!!!!!!!!!!!! None")
                LOG.error(type(npc_road_id))
                LOG.error(type(road_id))
                LOG.error(type(npc_lane_id))
                LOG.error(type(lane_id))
            # if int(npc_road_id) == int(road_id) and int(npc_lane_id) == int(lane_id):
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 10:
                if int(npc_road_id) == int(road_id) and int(npc_lane_id) != int(lane_id):
                    continue
                else:
                    is_npc_collision = True
                    break
        if is_npc_collision:
            continue
        for position in road_block_position:
            # if int(npc_road_id) == int(road_id) and int(npc_lane_id) == int(lane_id):
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 5:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        break

    LOG.info("add a NPC on road:{},lane:{},the position of it is {}, the behaviour is LaneFollow".format(road_id, lane_id, mid_point))
    new_npc = {}
    hash_value = hashlib.sha256(str(datetime.now()).encode("utf8"))
    uid = hash_value.hexdigest()[0:8] + "-" + hash_value.hexdigest()[9:13] + "-" + hash_value.hexdigest()[14:18] + "-" + hash_value.hexdigest()[19:23] + "-" + hash_value.hexdigest()[24:36]
    new_npc["uid"] = str(uid)
    new_npc["variant"] = ""
    new_npc["parameterType"] = ""
    new_npc["transform"] = {"position": None, "rotation": None}
    new_npc["transform"]["position"] = {"x": mid_point[0], "y": mid_point[2], "z": mid_point[1]}
    new_npc["transform"]["rotation"] = {"x": 0, "y": rotation, "z": 0}
    parameters = {"isLaneChange": False, "maxSpeed": 10}
    new_npc["behaviour"] = {"name": "NPCLaneFollowBehaviour", "parameters": parameters}
    new_npc["color"] = {"r": None, "g": None, "b": None}
    new_npc["waypoints"] = []
    new_one = NPCVehicle(new_npc)
    if is_bicycle:
        new_one.variant = "Bicyclist"
        new_one.agent_name = new_one.variant
    else:
        new_one = mut_npc_variant(new_one)
    new_one = mut_color(new_one)

    return new_one


def add_npc_waypoints(road_id_1, road_id_2, opendrive2apollo, ego_position, npc_position, road_block_position, is_bicycle):
    beg_road_id, beg_lane_id, begPosition = ego_position
    # todo(zero): only lane type is driving add relationship!!!
    path = []
    count = 0
    while True:
        s, rotation, mid_point, road_id, lane_id = opendrive2apollo.get_ran_road_point(int(road_id_1), "driving")
        if s == None:
            LOG.warning("Wrong road id {}".format(road_id_1))
            return None
        count += 1
        if count > 10:
            LOG.warning("Can't find a position to seat the NPC")
            return None
        # if int(beg_road_id) == int(road_id) and int(beg_lane_id) == int(lane_id):

        if math.sqrt((begPosition[0] - mid_point[0]) ** 2 + (begPosition[1] - mid_point[1]) ** 2) < 10:
            if not (int(beg_road_id) == int(road_id) and int(beg_lane_id) != int(lane_id)):
                continue
        is_npc_collision = False
        for position in npc_position:
            # if int(npc_road_id) == int(road_id) and int(npc_lane_id) == int(lane_id):
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 10:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        for position in road_block_position:
            # if int(npc_road_id) == int(road_id) and int(npc_lane_id) == int(lane_id):
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 5:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        break

    begin_point = (mid_point[0], mid_point[1], mid_point[2], rotation)
    speed = random.randint(6, 10)
    destination_point = (mid_point[0] + speed * math.cos(rotation) * 20, mid_point[1] + speed * math.sin(rotation) * 20, mid_point[2], rotation)
    LOG.info("add a linear NPC from ({}, {}), to ({}, {})".format(begin_point[0], begin_point[1], destination_point[0], destination_point[2]))
    waypoints = []

    position = {"x": destination_point[0], "y": destination_point[2], "z": destination_point[1]}
    rotation = {"x": 0, "y": destination_point[3], "z": 0}
    waypoint = {"ordinalNumber": 1, "position": position, "angle": rotation, "waitTime": 0, "speed": speed, "trigger": {"effectors": []}}
    waypoints.append(waypoint)
    new_npc = {}

    hash_value = hashlib.sha256(str(datetime.now()).encode("utf8"))
    uid = hash_value.hexdigest()[0:8] + "-" + hash_value.hexdigest()[9:13] + "-" + hash_value.hexdigest()[14:18] + "-" + hash_value.hexdigest()[19:23] + "-" + hash_value.hexdigest()[24:36]
    new_npc["uid"] = str(uid)
    new_npc["variant"] = ""
    new_npc["parameterType"] = ""
    new_npc["transform"] = {"position": None, "rotation": None}
    new_npc["transform"]["position"] = {"x": begin_point[0], "y": begin_point[2], "z": begin_point[1]}
    new_npc["transform"]["rotation"] = {"x": 0, "y": begin_point[3], "z": 0}
    parameters = {"isLaneChange": False, "maxSpeed": 10}
    new_npc["behaviour"] = {"name": "NPCWaypointBehaviour", "parameters": parameters}
    new_npc["color"] = {"r": None, "g": None, "b": None}
    new_npc["waypoints"] = waypoints
    new_one = NPCVehicle(new_npc)
    if is_bicycle:
        new_one.variant = "Bicyclist"
        new_one.agent_name = new_one.variant
    else:
        new_one = mut_npc_variant(new_one)
    new_one = mut_color(new_one)

    return new_one


def change_destination(opendrive2apollo, element, road_id_1=None):
    road_id_1 = random.sample(opendrive2apollo.road_id, 1)[0]
    s, rotation, mid_point, road_id, lane_id = opendrive2apollo.get_ran_road_point(int(road_id_1), "driving")

    count = 0
    while count < 20:
        count += 1
        begin_point_x = mid_point[0] + random.random() * 200
        begin_point_y = mid_point[1] + random.random() * 200
        is_in_road1, road_id_2, _ = opendrive2apollo.get_road_and_lane_id((begin_point_x, begin_point_y))
        if is_in_road1:
            break
    if not is_in_road1:
        road_id_2 = random.sample(opendrive2apollo.road_id, 1)[0]
    s2, rotation2, mid_point2, road_id2, lane_id2 = opendrive2apollo.get_ran_road_point(int(road_id_2), "driving")
    if s == None or s2 == None:
        LOG.warning("Wrong road id {}".format(road_id_1))
        return element

    LOG.info("change the destination of ego from {} to {}".format((element.destination.position), ({"x": mid_point[0], "y": mid_point[2], "z": mid_point[1]})))
    print(element.transform.position)
    element.transform.position = {"x": mid_point2[0], "y": mid_point2[2], "z": mid_point2[1]}
    element.transform.rotation = {"x": 0, "y": rotation2, "z": 0}
    print(element.transform.position)

    element.destination.position = {"x": mid_point[0], "y": mid_point[2], "z": mid_point[1]}
    element.destination.rotation = {"x": 0, "y": rotation, "z": 0}
    input("#")
    return element


def can_road_to_road(opendrive2apollo, begin_road_id, end_road_id, beg_lane_id=0):
    if beg_lane_id == 0:
        beg_lane = [1, -1]
    else:
        beg_lane = [beg_lane_id]
    for x in beg_lane:
        print("vertify one direction")
        path = opendrive2apollo.get_the_roads_path(begin_road_id, x, end_road_id, 1)
        if path is not None:
            return True
        path = opendrive2apollo.get_the_roads_path(begin_road_id, x, end_road_id, -1)
        if path is not None:
            return True
    return False


def add_immobile_npc(opendrive2apollo, npc_position, road_block_position, ego_position, is_bicycle, path=None):
    ego_point = ego_position[2]
    count = 0
    while count < 20:
        count += 1
        begin_point_x = ego_point[0] + random.random() * 100
        begin_point_y = ego_point[1] + random.random() * 100
        is_in_road1, road_id_1, _ = opendrive2apollo.get_road_and_lane_id((begin_point_x, begin_point_y))
        if is_in_road1:
            break
    if not is_in_road1:
        return None
    while True:
        s, rotation, mid_point, road_id, lane_id = opendrive2apollo.get_ran_road_point(int(road_id_1), "driving")
        if s == None:
            LOG.warning("Wrong road id {}".format(road_id_1))
            return None
        count += 1
        if count > 10:
            LOG.warning("Can't find a position to seat the NPC")
            return None
            # if int(beg_road_id) == int(road_id) and int(beg_lane_id) == int(lane_id):

        if math.sqrt((ego_point[0] - mid_point[0]) ** 2 + (ego_point[1] - mid_point[1]) ** 2) < 10:
            continue
        is_npc_collision = False
        for position in npc_position:
            # if int(npc_road_id) == int(road_id) and int(npc_lane_id) == int(lane_id):
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 10:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        for position in road_block_position:
            # if int(npc_road_id) == int(road_id) and int(npc_lane_id) == int(lane_id):
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 5:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        break

    begin_point = (mid_point[0], mid_point[1], mid_point[2], rotation)
    LOG.info("add an immobile NPC at x:{}, y:{}".format(begin_point[0], begin_point[1]))
    waypoints = []

    new_npc = {}

    hash_value = hashlib.sha256(str(datetime.now()).encode("utf8"))
    uid = hash_value.hexdigest()[0:8] + "-" + hash_value.hexdigest()[9:13] + "-" + hash_value.hexdigest()[14:18] + "-" + hash_value.hexdigest()[19:23] + "-" + hash_value.hexdigest()[24:36]
    new_npc["uid"] = str(uid)
    new_npc["variant"] = ""
    new_npc["parameterType"] = ""
    new_npc["transform"] = {"position": None, "rotation": None}
    new_npc["transform"]["position"] = {"x": begin_point[0], "y": begin_point[2], "z": begin_point[1]}
    new_npc["transform"]["rotation"] = {"x": 0, "y": begin_point[3], "z": 0}
    parameters = {"isLaneChange": False, "maxSpeed": 10}
    new_npc["behaviour"] = {"name": "NPCWaypointBehaviour", "parameters": parameters}
    new_npc["color"] = {"r": None, "g": None, "b": None}
    new_npc["waypoints"] = waypoints
    new_one = NPCVehicle(new_npc)
    if is_bicycle:
        new_one.variant = "Bicyclist"
        new_one.agent_name = new_one.variant
    else:
        new_one = mut_npc_variant(new_one)
    new_one = mut_color(new_one)

    return new_one


def add_waypoint_npc(opendrive2apollo, npc_position, road_block_position, ego_position, is_bicycle, path=None):
    ego_point = ego_position[2]
    count = 0
    while count < 20:
        count += 1
        begin_point_x = ego_point[0] + random.random() * 100
        begin_point_y = ego_point[1] + random.random() * 100
        is_in_road1, road_id1, _ = opendrive2apollo.get_road_and_lane_id((begin_point_x, begin_point_y))
        if is_in_road1:
            break
    if not is_in_road1:
        return None

    return add_npc_waypoints(road_id1, None, opendrive2apollo, ego_position, npc_position, road_block_position, is_bicycle)


def add_lane_follow_npc(opendrive2apollo, npc_position, road_block_position, ego_position, is_bicycle, path=None):
    ego_point = ego_position[2]
    count = 0
    while count < 11:
        count += 1
        begin_point_x = ego_point[0] + random.random() * 100
        begin_point_y = ego_point[1] + random.random() * 100
        is_in_road, road_id, lane_id = opendrive2apollo.get_road_and_lane_id((begin_point_x, begin_point_y))
        if is_in_road:
            break
    if count > 10:
        return None
    return add_npc_follow_lane(road_id, opendrive2apollo, ego_position, npc_position, road_block_position, is_bicycle)


def get_path(opendrive2apollo, element):
    beg_position = element.transform.position
    des_position = element.destination.position
    _, beg_road_id, beg_lane_id = opendrive2apollo.get_road_and_lane_id((beg_position["x"], beg_position["z"]))
    _, end_road_id, end_lane_id = opendrive2apollo.get_road_and_lane_id((des_position["x"], des_position["z"]))
    return opendrive2apollo.get_the_roads_path(beg_road_id, beg_lane_id, end_road_id, end_lane_id)


def add_walk_randomly_pedestrian(opendrive2apollo, pedestrian_first_position, ego_position):
    if len(opendrive2apollo.side_walk) == 0:
        return None
    beg_road_id, beg_lane_id, begPosition = ego_position
    road_id = random.sample(opendrive2apollo.side_walk, 1)[0]
    count = 0
    while True:
        s, rotation, mid_point, road_id, lane_id = opendrive2apollo.get_ran_road_point(int(road_id), "sidewalk")
        if s == None:
            LOG.warning("Wrong road id {}".format(road_id))
            return None
        count += 1
        if count > 100:
            LOG.warning("Can't find a position to seat the pedestrian")
            return None
        # if int(beg_road_id) == int(road_id) and int(beg_lane_id) == int(lane_id):
        is_npc_collision = False
        for position in pedestrian_first_position:
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 1:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        break

    LOG.info("add a NPC on road:{},lane:{},the position of it is {}, the behaviour is walk randomly".format(road_id, lane_id, mid_point))
    new_npc = {}
    hash_value = hashlib.sha256(str(datetime.now()).encode("utf8"))
    uid = hash_value.hexdigest()[0:8] + "-" + hash_value.hexdigest()[9:13] + "-" + hash_value.hexdigest()[14:18] + "-" + hash_value.hexdigest()[19:23] + "-" + hash_value.hexdigest()[24:36]
    new_npc["uid"] = str(uid)
    new_npc["variant"] = ""
    new_npc["parameterType"] = ""
    new_npc["transform"] = {"position": None, "rotation": None}
    new_npc["transform"]["position"] = {"x": mid_point[0], "y": mid_point[2], "z": mid_point[1]}
    new_npc["transform"]["rotation"] = {"x": 0, "y": rotation, "z": 0}
    new_npc["behaviour"] = "Walk_randomly"
    new_npc["waypoints"] = []
    new_one = Pedestrian(new_npc)
    new_one = mut_ped_variant(new_one)

    return new_one


def add_cross_road_pedestrian(opendrive2apollo, pedestrian_first_position, ego_position, path):
    beg_road_id, beg_lane_id, begPosition = ego_position
    count = 0
    while count < 11:
        count += 1
        begin_point_x = begPosition[0] + random.random() * 100
        begin_point_y = begPosition[1] + random.random() * 100
        is_in_road, road_id, lane_id = opendrive2apollo.get_road_and_lane_id((begin_point_x, begin_point_y))
        if is_in_road:
            break
    if not is_in_road:
        return None
    while True:
        _, _, begin_position, end_position = opendrive2apollo.cross_road_waypoint(road_id)
        count += 1
        if count > 30:
            LOG.warning("Can't find a palce to seat the pedstrian!")
            return None
        is_npc_collision = False
        for position in pedestrian_first_position:
            if math.sqrt((begin_position[0] - position[0]) ** 2 + (begin_position[1] - position[1]) ** 2) < 1:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        break
    LOG.info(
        "add a NPC on the side of the road:{},the position of it is {}, and the destination of it is {} \
             the behaviour is cross road".format(
            road_id, (begin_position[0], begin_position[2], begin_position[1]), (end_position[0], end_position[2], end_position[1])
        )
    )
    waypoints = []
    speed = random.randint(1, 4)
    waitdistance = random.randint(5, 20)
    position = {"x": begin_position[0], "y": begin_position[2], "z": begin_position[1]}
    angle = {"x": 0, "y": begin_position[3], "z": 0}
    waypoint = {
        "ordinalNumber": 0,
        "position": position,
        "angle": angle,
        "waitTime": 0,
        "speed": speed,
        "trigger": {"effectors": [{"typeName": "WaitForDistance", "parameters": {"maxDistance": waitdistance}}]},
    }
    waypoints.append(waypoint)

    position = {"x": end_position[0], "y": end_position[2], "z": end_position[1]}
    angle = {"x": 0, "y": end_position[3], "z": 0}
    waypoint = {"ordinalNumber": 1, "position": position, "angle": angle, "waitTime": 0, "speed": speed, "trigger": {"effectors": []}}
    waypoints.append(waypoint)

    new_npc = {}
    hash_value = hashlib.sha256(str(datetime.now()).encode("utf8"))
    uid = hash_value.hexdigest()[0:8] + "-" + hash_value.hexdigest()[9:13] + "-" + hash_value.hexdigest()[14:18] + "-" + hash_value.hexdigest()[19:23] + "-" + hash_value.hexdigest()[24:36]
    new_npc["uid"] = str(uid)
    new_npc["variant"] = ""
    new_npc["parameterType"] = ""
    new_npc["transform"] = {"position": None, "rotation": None}
    new_npc["transform"]["position"] = {"x": begin_position[0], "y": begin_position[2], "z": begin_position[1]}
    new_npc["transform"]["rotation"] = {"x": 0, "y": begin_position[3], "z": 0}
    new_npc["behaviour"] = "WaypointBehaviour"
    new_npc["waypoints"] = waypoints
    new_one = Pedestrian(new_npc)
    new_one = mut_ped_variant(new_one)

    return new_one


def add_roadblock(opendrive2apollo, NPC_first_position, road_block_position, ego_position):
    beg_road_id, beg_lane_id, begPosition = ego_position
    road_id = random.sample(opendrive2apollo.road_id, 1)[0]
    count = 0
    while True:
        s, rotation, mid_point, road_id, lane_id = opendrive2apollo.get_ran_road_point(int(road_id), "driving")
        if s == None:
            LOG.warning("Wrong road id {}".format(road_id))
            return None
        count += 1
        if count > 100:
            LOG.warning("Can't find a position to seat the road block")
            return None

        is_npc_collision = False
        if math.sqrt((begPosition[0] - mid_point[0]) ** 2 + (begPosition[1] - mid_point[1]) ** 2) < 5:
            if not (int(beg_road_id) == int(road_id) and int(beg_lane_id) != int(lane_id)):
                continue
        for position in road_block_position:
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 1:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        for position in NPC_first_position:
            if math.sqrt((mid_point[0] - position[0]) ** 2 + (mid_point[1] - position[1]) ** 2) < 5:
                is_npc_collision = True
                break
        if is_npc_collision:
            continue
        break
    LOG.info("add a road block on road:{},lane:{},the position of it is {}".format(road_id, lane_id, mid_point))
    new_block = {}
    hash_value = hashlib.sha256(str(datetime.now()).encode("utf8"))
    uid = hash_value.hexdigest()[0:8] + "-" + hash_value.hexdigest()[9:13] + "-" + hash_value.hexdigest()[14:18] + "-" + hash_value.hexdigest()[19:23] + "-" + hash_value.hexdigest()[24:36]
    new_block["uid"] = str(uid)
    new_block["name"] = "TrafficCone"
    new_block["policy"] = [{"action": "state", "value": ""}]
    new_block["transform"] = {"position": None, "rotation": None}
    new_block["transform"]["position"] = {"x": mid_point[0], "y": mid_point[2], "z": mid_point[1]}
    new_block["transform"]["rotation"] = {"x": 0, "y": rotation, "z": 0}
    new_one = StaticObstacle(new_block)

    return new_one
