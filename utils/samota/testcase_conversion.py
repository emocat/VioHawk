import math
import copy
import os
import sys
import json
import uuid
import numpy as np
from shapely.geometry import Point, LineString, Polygon, GeometryCollection
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import dataparser
from utils import helper
from utils import map_helper

def get_four_wheel_position(position: dict, rotation: dict) -> list:
    wheel = []
    length = 2.835 / 2
    width = 1.66 / 2
    l2 = length * length + width * width
    l = np.sqrt(l2)
    sina = width / l
    degree = np.radians(rotation["y"])

    a = math.asin(sina)
    b = degree
    x = position["x"]
    y = position["z"]

    w1_x = l * np.sin(a + b) + x
    w1_y = l * np.cos(a + b) + y
    wheel.append([w1_x, w1_y])
    w2_x = l * np.sin(b - a) + x
    w2_y = l * np.cos(b - a) + y
    wheel.append([w2_x, w2_y])
    w3_x = l * np.sin(b + math.pi - a) + x
    w3_y = l * np.cos(b + math.pi - a) + y
    wheel.append([w3_x, w3_y])
    w4_x = l * np.sin(b + math.pi + a) + x
    w4_y = l * np.cos(b + math.pi + a) + y
    wheel.append([w4_x, w4_y])

    return wheel

def get_wheel_center(wheel: list) -> list:
    center_x = sum([point[0] for point in wheel]) / len(wheel)
    center_y = sum([point[1] for point in wheel]) / len(wheel)
    return [center_x, center_y]

def get_lane_index(lane_id):
    index = int(lane_id[5:])
    return index

def calculate_robustness(traces,map_info,scenario_class):
    scenario = scenario_class.json_obj
    dist_center_lane = 1
    dist_min_other_vehicle = 1
    dist_min_pedestrian = 1
    dist_min_mesh = 1
    dist_from_final_destnation = 1

    DfC_min = 1
    DfV_min = 1
    DfP_min = 1
    DfM_min = 1
    DT_max = 1
    traffic_lights_max = 1

    destination_point = None
    for agent in scenario["agents"]:
        if agent["type"] == 1:
            destination_point = Point(agent["destinationPoint"]["position"]["x"], agent["destinationPoint"]["position"]["z"])
            break

    passed_points = []
    for trace in traces:
        ego_position = trace["EGO"]["Position"]
        ego_rotation = trace["EGO"]["Rotation"]
        ego_wheel = get_four_wheel_position(ego_position, ego_rotation)

        ego_position_x = trace["EGO"]["Position"]["x"]
        ego_position_y = trace["EGO"]["Position"]["z"]
        ego_polygon = Polygon(ego_wheel)

        # dist_center_lane
        ego_center = get_wheel_center(ego_wheel)
        ego_center_point = Point(ego_center)

        ego_lane = map_info.find_which_area_the_point_is_in((ego_position_x, ego_position_y))
        if 'lane_id' in ego_lane[0] and ego_lane[0]["laneNumber"] > 1: 
            central_curve_points = map_info.lane_waypoints[ego_lane[0]['lane_id']]   
            central_line = LineString(central_curve_points)
            dist_center_lane = central_line.distance(ego_center_point)
            if dist_center_lane < DfC_min:
                DfC_min = dist_center_lane

        # dist_min_other_vehicle
        # for NPC in trace["NPCs"]:
        #     if NPC["Label"] != "Pedestrian":
        #         NPC_position = NPC["Position"]
        #         NPC_rotation = NPC["Rotation"]
        #         NPC_wheel = get_four_wheel_position(NPC_position, NPC_rotation)
        #         NPC_position_x = NPC_position["x"]
        #         NPC_position_y = NPC_position["z"]

        #         NPC_lane = map_info.find_which_area_the_point_is_in((NPC_position_x, NPC_position_y))
        #         if 'lane_id' in NPC_lane[0] and NPC_lane[0]["laneNumber"] > 1:
        #             if 'lane_id' in ego_lane[0] and ego_lane[0]["laneNumber"] > 1 and NPC_lane[0]["lane_id"] == ego_lane[0]["lane_id"]:
        #                 NPC_polygon = Polygon(NPC_wheel)
        #                 dist_min_other_vehicle = NPC_polygon.distance(ego_polygon)
        #                 if dist_min_other_vehicle < DfV_min:
        #                     DfV_min = dist_min_other_vehicle
        # dist_min_other_vehicle
        NPC_in_front_id = None
        if trace["Sequence"] == 0:
            for NPC in trace["NPCs"]:
                if NPC["Label"] != "Pedestrian":
                    NPC_position = NPC["Position"]
                    NPC_rotation = NPC["Rotation"]
                    NPC_wheel = get_four_wheel_position(NPC_position, NPC_rotation)
                    NPC_position_x = NPC_position["x"]
                    NPC_position_y = NPC_position["z"]
                    NPC_lane = map_info.find_which_area_the_point_is_in((NPC_position_x, NPC_position_y))
                    if 'lane_id' in NPC_lane[0] and NPC_lane[0]["laneNumber"] > 1:
                        if NPC_lane[0]["lane_id"] == ego_lane[0]["lane_id"]:
                            NPC_in_front_id = NPC["Id"]
                            break
        if NPC_in_front_id != None:
            for NPC in trace["NPCs"]:
                if NPC["Id"] == NPC_in_front_id:
                    NPC_position = NPC["Position"]
                    NPC_rotation = NPC["Rotation"]
                    NPC_wheel = get_four_wheel_position(NPC_position, NPC_rotation)
                    NPC_polygon = Polygon(NPC_wheel)
                    dist_min_other_vehicle = NPC_polygon.distance(ego_polygon)
                    if dist_min_other_vehicle < DfV_min:
                        DfV_min = dist_min_other_vehicle
                    break
        #  dist_min_pedestrian
        for NPC in trace["NPCs"]:
            if NPC["Label"] == "Pedestrian":
                NPC_position_x = NPC["Position"]["x"]
                NPC_position_y = NPC["Position"]["z"]
                NPC_position = Point(NPC_position_x, NPC_position_y)
                dist_min_pedestrian = NPC_position.distance(ego_polygon)
                if dist_min_pedestrian < DfP_min:
                    DfP_min = dist_min_pedestrian

        # dist_min_mesh
        for traffic_light in map_info.traffic_signals:
            traffic_light_position = Point(traffic_light["point"]["x"], traffic_light["point"]["z"])
            dist_min_mesh = traffic_light_position.distance(ego_polygon)
            if dist_min_mesh < DfM_min:
                DfM_min = dist_min_mesh
        
        # dist_from_final_destnation
        passed_points.append(ego_center_point)
        if len(passed_points) < 2:
            passed_dist = 0
        else:
            passed_dist = LineString(passed_points).length
        remaining_dist = ego_center_point.distance(destination_point)
        dist_from_final_destnation = passed_dist / (passed_dist+remaining_dist)
        if dist_from_final_destnation > DT_max:
            DT_max = dist_from_final_destnation

        # traffic_lights_max
        detected_signals = trace["Traffic_Lights"]
        for detected_signal in detected_signals:
            detected_signal_color = detected_signal["Label"]
            detected_signal_point_x = detected_signal["Position"]["x"]
            detected_signal_point_y = detected_signal["Position"]["z"]
            detected_signal_point = Point(detected_signal_point_x , detected_signal_point_y)

            if detected_signal_color == "red":
                #get nearest junction from signal
                id = None
                min_dis = 1000
                for key in map_info.areas["junction_areas"]:
                    points = []
                    points = map_info.areas["junction_areas"][key]
                    the_area = Polygon(points)
                    if the_area.distance(detected_signal_point) < min_dis:
                        min_dis = ego_polygon.distance(detected_signal_point)
                        id = key
                junction_poygon = Polygon(map_info.areas["junction_areas"][id])

                if junction_poygon.contains(ego_center_point):
                    traffic_lights_max = 0
    # result                
    DfC = 1 - (DfC_min / 1.15)
    DfV = min(1,DfV_min)
    DfP = min(1,DfP_min)
    DfM = min(1,DfM_min)    
    DT =  min(1,DT_max)
    traffic_lights = min(1,traffic_lights_max)

    return [DfC,DfV,DfP,DfM,DT,traffic_lights]


def add_npc_vehicle(position,rotation,variant):
    uid = str(uuid.uuid4())
    new_vehicle = {
        "uid": uid,
        "variant": variant,
        "type": 2,
        "parameterType": "",
        "transform": {
            "position": {
                "x": position[0],
                "y": position[1],
                "z": position[2]
            },
            "rotation": {
                "x": rotation[0],
                "y": rotation[1],
                "z": rotation[2]
            }
        },
        "behaviour": {
            "name": "NPCLaneFollowBehaviour",
            "parameters": {
                "isLaneChange": False,
                "maxSpeed": 0
            }
        },
        "color": {
            "r": 0.0141509473323822,
            "g": 0.249999970197678,
            "b": 0.0235849004238844
        },
        "waypoints": []
    }
    return new_vehicle
    

def decode_to_json(session, scenario_class, test_list):
    # '√'——finish  'x'——not need  '-'——not finish

    # 0 Road type ×
    # 1 Road ID ×
    # 2 Scenario Length √
    # 3 Vehicle_in_front -
    # 4 vehicle_in_adjcent_lane -
    # 5 vehicle_in_opposite_lane -
    # 6 vehicle_in_front_two_wheeled √
    # 7 vehicle_in_adjacent_two_wheeled √
    # 8 vehicle_in_opposite_two_wheeled √
    # 9 time of day √
    # 10 weather √
    # 11 Number of People ×
    # 12 Target Speed √
    # 13 Trees in scenario ×
    # 14 Buildings in Scenario ×
    # 15 task ×
    scenario = scenario_class.json_obj
    # Set Road 
    vechicle_in_front_position = None
    vechicle_in_adjcent_lane_position = None
    vechicle_in_opposite_lane_position = None
    vechicle_in_front_rotation = None
    vechicle_in_adjcent_lane_rotation = None
    vechicle_in_opposite_lane_rotation = None 

# Set Vehicle ID
    if session == "car_stop_at_crosswalk_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.786911010742,10.2076635360718,210.683303833008)
        vechicle_in_front_rotation = (0,359.976470947266,0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.807678222656,10.2076644897461,210.950881958008)
        vechicle_in_adjcent_lane_rotation = (0, 0.0544324144721031, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.847091674805, 10.2076635360718, 210.253692626953)
        vechicle_in_opposite_lane_rotation = (0, 179.969482421875, 0) 
    elif session == "car_stop_at_crosswalk_T_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.860549926758, 10.2076635360718, -59.7946166992188)
        vechicle_in_front_rotation = (0, 359.691833496094, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.860931396484, 10.2076635360718, -59.9786262512207)
        vechicle_in_adjcent_lane_rotation = (0, 0.019092695787549, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.795562744141, 10.2076635360718, -59.660083770752)
        vechicle_in_opposite_lane_rotation = (3.96478390030097e-06, 180.329742431641, 7.95138679647378e-16)  
    elif session == "car_stop_at_crosswalk_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-163.547897338867, 10.2076644897461, -26.6197776794434)
        vechicle_in_front_rotation = (7.85860436280927e-07, 270.047332763672, 2.54444377487161e-14)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-163.288711547852, 10.2076635360718, -30.7282428741455)
        vechicle_in_adjcent_lane_rotation = (7.85532108693587e-07, 270.132598876953, 2.54444377487161e-14)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-163.039855957031, 10.2076635360718, -34.5972213745117)
        vechicle_in_opposite_lane_rotation = (0, 89.8031539916992, 0)
    elif session == "car_stop_at_crosswalk_Y_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.87646484375, 10.2076635360718, -475.056518554688)
        vechicle_in_front_rotation = (0, 359.910705566406, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.8203125, 10.2076635360718, -475.322479248047)
        vechicle_in_adjcent_lane_rotation = (0, -0.00198501464910805, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.860214233398, 10.2076635360718, -475.321350097656)
        vechicle_in_opposite_lane_rotation = (0, 180.151626586914, 0)
    elif session == "car_stop_at_crosswalk_Y_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-223.299911499023, 10.2076635360718, -430.954010009766)
        vechicle_in_front_rotation = (0, 120.621658325195, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-224.175842285156, 10.2076635360718, -435.074584960938)
        vechicle_in_adjcent_lane_rotation = (0, 120.290916442871, 0)
        # vechicle_in_opposite_lane
            # none
    elif session == "overtaking_four_lanes_straight":
        # vechicle_in_front
        vechicle_in_front_position = (382.811492919922, 10.207633972168, 167.888626098633)
        vechicle_in_front_rotation = (0, 0.000190020058653317, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (378.751434326172, 10.207633972168, 154.427703857422)
        vechicle_in_adjcent_lane_rotation = (0, 0.000157417147420347, 0)
        # vechicle_in_opposite_lane
            # none
    elif session == "park_at_crosswalk_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.786804199219, 10.2076635360718, 210.437713623047)
        vechicle_in_front_rotation = (0, 359.976470947266, 0)
        # vechicle_in_adjcent_lane 
        vechicle_in_adjcent_lane_position = (-189.807800292969, 10.2076635360718, 210.814849853516)
        vechicle_in_adjcent_lane_rotation = (0, 0.0544324144721031, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.847183227539, 10.2076635360718, 210.437759399414)
        vechicle_in_opposite_lane_rotation = (0, 179.969482421875, 0)
    elif session == "park_at_crosswalk_T_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.865249633789, 10.2076635360718, -58.9212417602539)
        vechicle_in_front_rotation = (0, 359.691833496094, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.860656738281, 10.2076635360718, -59.1337776184082)
        vechicle_in_adjcent_lane_rotation = (0, 0.019092695787549, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.793151855469, 10.2076635360718, -59.2405700683594)
        vechicle_in_opposite_lane_rotation = (3.96478390030097e-06, 180.329742431641, 7.95138679647378e-16)
    elif session == "park_at_crosswalk_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-165.504913330078, 10.2076644897461, -26.6181602478027)
        vechicle_in_front_rotation = (7.85860436280927e-07, 270.047332763672, 2.54444377487161e-14)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-165.50390625, 10.2076635360718, -30.7231159210205)
        vechicle_in_adjcent_lane_rotation = (7.85532051850169e-07, 270.132598876953, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-165.418731689453, 10.2076635360718, -34.6053924560547)
        vechicle_in_opposite_lane_rotation = (0, 89.8031539916992, 0)
    elif session == "park_at_crosswalk_Y_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.881225585938, 10.2076635360718, -471.99658203125)
        vechicle_in_front_rotation = (0, 359.910705566406, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.820419311523, 10.2076635360718, -472.196319580078)
        vechicle_in_adjcent_lane_rotation = (0, -0.00198501464910805, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.852005004883, 10.2076635360718, -472.221282958984)
        vechicle_in_opposite_lane_rotation = (0, 180.151626586914, 0)
    elif session == "park_at_crosswalk_Y_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-223.299911499023, 10.2076635360718, -430.954010009766)
        vechicle_in_front_rotation = (0, 120.621658325195, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-225.352157592773, 10.2076635360718, -434.387481689453)
        vechicle_in_adjcent_lane_rotation = (0, 120.290916442871, 0)
        # vechicle_in_opposite_lane
            # none
    elif session == "park_near_crosswalk_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.786804199219, 10.2076635360718, 210.437713623047)
        vechicle_in_front_rotation = (0, 359.976470947266, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.807800292969, 10.2076635360718, 210.814849853516)
        vechicle_in_adjcent_lane_rotation = (0, 0.0544324144721031, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.847274780273, 10.2076635360718, 210.606140136719)
        vechicle_in_opposite_lane_rotation = (0, 179.969482421875, 0)
    elif session == "park_near_crosswalk_T_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.836349487305, 10.2076635360718, -64.2934036254883)
        vechicle_in_front_rotation = (0, 359.691833496094, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.862518310547, 10.2076635360718, -64.749153137207)
        vechicle_in_adjcent_lane_rotation = (0, 0.019092695787549, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.821334838867, 10.2076644897461, -64.1382522583008)
        vechicle_in_opposite_lane_rotation = (3.96478390030097e-06, 180.329742431641, 7.95138679647378e-16)
    elif session == "park_near_crosswalk_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-160.595275878906, 10.2076635360718, -26.6222152709961)
        vechicle_in_front_rotation = (7.85860436280927e-07, 270.047332763672, 2.54444377487161e-14)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-160.556396484375, 10.2076635360718, -30.7345657348633)
        vechicle_in_adjcent_lane_rotation = (7.85532108693587e-07, 270.132598876953, 2.54444377487161e-14)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-160.710952758789, 10.2076635360718, -34.5892181396484)
        vechicle_in_opposite_lane_rotation = (0, 89.8031539916992, 0)
    elif session == "park_near_crosswalk_Y_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.877777099609, 10.2076635360718, -474.21435546875)
        vechicle_in_front_rotation = (0, 359.910705566406, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.820358276367, 10.2076635360718, -474.024658203125)
        vechicle_in_adjcent_lane_rotation = (0, -0.00198501464910805, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.856918334961, 10.2076635360718, -474.076690673828)
        vechicle_in_opposite_lane_rotation = (0, 180.151626586914, 0)
    elif session == "park_near_crosswalk_Y_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-224.97624206543, 10.2076635360718, -429.961791992188)
        vechicle_in_front_rotation = (0, 120.621658325195, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-225.973739624023, 10.2076635360718, -434.024383544922)
        vechicle_in_adjcent_lane_rotation = (0, 120.290916442871, 0)
        # vechicle_in_opposite_lane
            # none
    elif session == "park_near_signal_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.89958190918, 10.2076635360718, 221.615142822266)
        vechicle_in_front_rotation = (0, 359.976470947266, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.807159423828, 10.2076644897461, 211.494430541992)
        vechicle_in_adjcent_lane_rotation = (0, 0.0544324144721031, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.847702026367, 10.2076635360718, 211.391418457031)
        vechicle_in_opposite_lane_rotation = (0, 179.969482421875, 0)    
    elif session == "park_near_signal_T_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.549026489258, 10.2076644897461, -42.4943084716797)
        vechicle_in_front_rotation = (0, 359.691833496094, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.860778808594, 10.2076635360718, -59.5004997253418)
        vechicle_in_adjcent_lane_rotation = (0, 0.019092695787549, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.794677734375, 10.2076635360718, -59.5060386657715)
        vechicle_in_opposite_lane_rotation = (3.96478390030097e-06, 180.329742431641, 7.95138679647378e-16)
    elif session == "park_near_signal_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-189.7021484375, 10.2076635360718, -19.3634605407715)
        vechicle_in_front_rotation = (0, 0.0346142500638962, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-165.536956787109, 10.2076635360718, -30.7230396270752)
        vechicle_in_adjcent_lane_rotation = (7.8553199500675e-07, 270.132598876953, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-165.537689208984, 10.2076635360718, -34.6058006286621)
        vechicle_in_opposite_lane_rotation = (0, 89.8031539916992, 0) 
    elif session == "park_near_signal_Y_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.885986328125, 10.2076635360718, -468.936828613281)
        vechicle_in_front_rotation = (0, 359.910705566406, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.820526123047, 10.2076635360718, -469.084106445313)
        vechicle_in_adjcent_lane_rotation = (0, -0.00198501464910805, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.851989746094, 10.2076635360718, -472.219085693359)
        vechicle_in_opposite_lane_rotation =(0, 180.151626586914, 0)
    elif session == "park_near_signal_Y_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-224.97624206543, 10.2076635360718, -429.961791992188)
        vechicle_in_front_rotation = (0, 120.621658325195, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-225.973739624023, 10.2076635360718, -434.024383544922)
        vechicle_in_adjcent_lane_rotation = (0, 120.290916442871, 0)
        # vechicle_in_opposite_lane
            # none
    elif session == "park_near_stop_sign_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-21.3529186248779, 10.2076635360718, -38.5354690551758)
        vechicle_in_front_rotation = (0, 89.9501190185547, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-20.0038280487061, 10.2076635360718, -34.3328666687012)
        vechicle_in_adjcent_lane_rotation = (0, 89.9679183959961, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-22.2588520050049, 10.2076635360718, -30.7885761260986)
        vechicle_in_opposite_lane_rotation =(0, 269.933868408203, 0)
    elif session == "pedestrian_at_crosswalk_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-166.220291137695, 10.2076635360718, 341.487213134766)
        vechicle_in_front_rotation = (0, 271.192260742188, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-166.092880249023, 10.2076635360718, 345.335174560547)
        vechicle_in_adjcent_lane_rotation = (0, 270.942535400391, 0)
        # vechicle_in_opposite_lane
            # none
    elif session == "pedestrian_at_crosswalk_T_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.861587524414, 10.2076635360718, -59.6014137268066)
        vechicle_in_front_rotation = (0, 359.691833496094, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.860748291016, 10.2076635360718, -59.4100341796875)
        vechicle_in_adjcent_lane_rotation = (0, 0.019092695787549, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.795364379883, 10.2076635360718, -59.6246337890625)
        vechicle_in_opposite_lane_rotation =(3.96478390030097e-06, 180.329742431641, 7.95138679647378e-16)
    elif session == "pedestrian_at_crosswalk_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-165.587493896484, 10.2076635360718, -26.618091583252)
        vechicle_in_front_rotation = (7.85860436280927e-07, 270.047332763672, 2.54444377487161e-14)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-165.222961425781, 10.2076635360718, -30.7237663269043)
        vechicle_in_adjcent_lane_rotation = (7.85532051850169e-07, 270.132598876953, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-164.591430664063, 10.2076644897461, -34.6025505065918)
        vechicle_in_opposite_lane_rotation = (0, 89.8031539916992, 0)
    elif session == "pedestrian_at_crosswalk_Y_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.881408691406, 10.2076635360718, -471.885375976563)
        vechicle_in_front_rotation = (0, 359.910705566406, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.820434570313, 10.2076635360718, -471.886474609375)
        vechicle_in_adjcent_lane_rotation = (0, -0.00198501464910805, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.85075378418, 10.2076635360718, -471.751281738281)
        vechicle_in_opposite_lane_rotation = (0, 180.151626586914, 0)
    elif session == "pedestrian_at_crosswalk_Y_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-223.299911499023, 10.2076635360718, -430.954010009766)
        vechicle_in_front_rotation = (0, 120.621658325195, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-225.352157592773, 10.2076635360718, -434.387481689453)
        vechicle_in_adjcent_lane_rotation = (0, 120.290916442871, 0)
        # vechicle_in_opposite_lane
            # none
    elif session == "pedestrian_at_crosswalk_turning_side_C_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-189.807525634766, 10.2076635360718, 211.108261108398)
        vechicle_in_front_rotation = (0, 0.0544324144721031, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-193.787063598633, 10.2076635360718, 211.066711425781)
        vechicle_in_adjcent_lane_rotation = (0, 359.976470947266, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.847396850586, 10.2076635360718, 210.834213256836)
        vechicle_in_opposite_lane_rotation = (0, 179.969482421875, 0)
    elif session == "pedestrian_at_crosswalk_turning_side_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-165.587493896484, 10.2076635360718, -26.618091583252)
        vechicle_in_front_rotation = (7.85860436280927e-07, 270.047332763672, 2.54444377487161e-14)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-165.222961425781, 10.2076635360718, -30.7237663269043)
        vechicle_in_adjcent_lane_rotation = (7.85532108693587e-07, 270.132598876953, 2.54444377487161e-14)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-164.995361328125, 10.2076635360718, -34.6039390563965)
        vechicle_in_opposite_lane_rotation = (0, 89.8031539916992, 0)
    elif session == "traffic_light_red_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.786834716797,10.2076635360718,210.520889282227)
        vechicle_in_front_rotation = (0,359.976470947266,0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.808090209961,10.2076635360718,210.520034790039)
        vechicle_in_adjcent_lane_rotation = (0,0.0544324144721031,0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.847198486328,10.2076635360718,210.442047119141)
        vechicle_in_opposite_lane_rotation = (0,179.969482421875,0)
    elif session == "traffic_light_red_T_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.864501953125,10.2076635360718,-59.0592231750488)
        vechicle_in_front_rotation = (0,359.691833496094,0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.860626220703,10.2076635360718,-59.047306060791)
        vechicle_in_adjcent_lane_rotation = (0,0.019092695787549,0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.789108276367,10.2076635360718,-58.5383224487305)
        vechicle_in_opposite_lane_rotation = (3.96478435504832E-06,180.329742431641,7.95138679647378E-16)      
    elif session == "traffic_light_red_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-164.375305175781,10.2076635360718,-26.6190929412842)
        vechicle_in_front_rotation = (7.85860436280927E-07,270.047332763672,2.54444377487161E-14)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-164.278366088867,10.2076635360718,-30.7259521484375)
        vechicle_in_adjcent_lane_rotation = (7.8553199500675E-07,270.132598876953,0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-163.261474609375,10.2076635360718,-34.5979804992676)
        vechicle_in_opposite_lane_rotation = (0,89.8031539916992,0) 
    elif session == "traffic_light_red_Y_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.880126953125,10.2076635360718,-472.706024169922)
        vechicle_in_front_rotation = (0,359.910705566406,0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.820373535156,10.2076635360718,-473.608367919922)
        vechicle_in_adjcent_lane_rotation = (0,-0.00198501464910805,0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.861862182617,10.2076644897461,-475.945373535156)
        vechicle_in_opposite_lane_rotation = (0,180.151626586914,0) 
    elif session == "traffic_light_red_Y_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-223.218490600586,10.2076635360718,-431.002197265625)
        vechicle_in_front_rotation = (0,120.621658325195,0)
        # vechicle_in_adjcent_lane
        vechicle_in_opposite_lane_position = (-225.034423828125, 10.2076635360718, -434.573059082031)
        vechicle_in_opposite_lane_rotation = (0, 120.290916442871, 0) 
        # vechicle_in_opposite_lane
            # none
    elif session == "traffic_light_yellow_C_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.786636352539, 10.2076635360718, 210.021072387695)
        vechicle_in_front_rotation = (0, 359.976470947266, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.808303833008, 10.2076644897461, 210.286926269531)
        vechicle_in_adjcent_lane_rotation = (0, 0.0544324144721031, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.847320556641, 10.2076635360718, 210.680541992188)
        vechicle_in_opposite_lane_rotation = (0, 179.969482421875, 0)
    elif session == "traffic_light_yellow_T_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-201.809005737305, 10.2076635360718, -6.60836172103882)
        vechicle_in_front_rotation = (0, 180.044143676758, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-197.69108581543, 10.2076635360718, -6.5786280632019)
        vechicle_in_adjcent_lane_rotation = (0, 179.942749023438, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-193.694549560547, 10.2076635360718, -6.74467658996582)
        vechicle_in_opposite_lane_rotation = (0, 359.941375732422, 0)      
    elif session == "traffic_light_yellow_T_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-163.547897338867, 10.2076644897461, -26.6197776794434)
        vechicle_in_front_rotation = (7.85860436280927e-07, 270.047332763672, 2.54444377487161e-14)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-163.529312133789, 10.2076635360718, -30.7276859283447)
        vechicle_in_adjcent_lane_rotation = (7.8553199500675e-07, 270.132598876953, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-163.204772949219, 10.2076635360718, -34.597785949707)
        vechicle_in_opposite_lane_rotation = (0, 89.8031539916992, 0) 
    elif session == "traffic_light_yellow_Y_straight":
        # vechicle_in_front
        vechicle_in_front_position = (-193.879699707031, 10.2076635360718, -472.978637695313)
        vechicle_in_front_rotation = (0, 359.910705566406, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_adjcent_lane_position = (-189.820373535156, 10.2076635360718, -473.467803955078)
        vechicle_in_adjcent_lane_rotation = (0, -0.00198501464910805, 0)
        # vechicle_in_opposite_lane
        vechicle_in_opposite_lane_position = (-197.85334777832, 10.2076635360718, -472.73095703125)
        vechicle_in_opposite_lane_rotation = (0, 180.151626586914, 0)
    elif session == "traffic_light_yellow_Y_turning":
        # vechicle_in_front
        vechicle_in_front_position = (-224.196228027344, 10.2076635360718, -430.423492431641)
        vechicle_in_front_rotation = (0, 120.621658325195, 0)
        # vechicle_in_adjcent_lane
        vechicle_in_opposite_lane_position = (-225.643173217773, 10.2076635360718, -434.217468261719)
        vechicle_in_opposite_lane_rotation = (0, 120.290916442871, 0) 
        # vechicle_in_opposite_lane
            # none
    else:
        print("session error")  

    # Reset Vehicle
    if "agents" not in scenario:
        scenario["agents"] = []
    else:
        agents_to_remove = []
        for agent in scenario["agents"]:
            if agent["type"] == 2: 
                agents_to_remove.append(agent)

        for agent in agents_to_remove:
            scenario["agents"].remove(agent)


    # if test_list[3] == 1 and vechicle_in_front_position != None: # Vehicle in front
    if (session.startswith("traffic_light_yellow") or session.startswith("pedestrian_at_crosswalk") or test_list[3] == 1) and vechicle_in_front_position != None: # Vehicle in front
        if test_list[6] == 0:
            new_vehicle = add_npc_vehicle(vechicle_in_front_position,vechicle_in_front_rotation,variant="SUV")
            scenario["agents"].append(new_vehicle)
        elif test_list[6] == 1:
            new_vehicle = add_npc_vehicle(vechicle_in_front_position,vechicle_in_front_rotation,variant="Bicyclist")
            scenario["agents"].append(new_vehicle)
        else:
            print("vehicle type error")  

    if test_list[4] == 1 and vechicle_in_adjcent_lane_position != None: # Vehicle in adjacent lane
        if test_list[7] == 0:
            new_vehicle = add_npc_vehicle(vechicle_in_adjcent_lane_position,vechicle_in_adjcent_lane_rotation,variant="SUV")
            scenario["agents"].append(new_vehicle)
        elif test_list[7] == 1:
            new_vehicle = add_npc_vehicle(vechicle_in_adjcent_lane_position,vechicle_in_adjcent_lane_rotation,variant="Bicyclist")
            scenario["agents"].append(new_vehicle)
        else:
            print("vehicle type error") 

    if test_list[5] == 1 and vechicle_in_opposite_lane_position != None: # Vehicle in opposite lane
        if test_list[8] == 0:
            new_vehicle = add_npc_vehicle(vechicle_in_opposite_lane_position,vechicle_in_opposite_lane_rotation,variant="SUV")
            scenario["agents"].append(new_vehicle)
        elif test_list[8] == 1:
            new_vehicle = add_npc_vehicle(vechicle_in_opposite_lane_position,vechicle_in_opposite_lane_rotation,variant="Bicyclist")
            scenario["agents"].append(new_vehicle)
        else:
            print("vehicle type error") 

    # Set Time
    if "time" not in scenario:
        scenario["time"] = {
            "year": 2022,
            "month": 10,
            "day": 25,
            "hour": 15,
            "minute": 30,
            "second": 0
        }
    if test_list[9] == 0:
        scenario["time"]["hour"] = 12
        scenario["time"]["minute"] = 0
    elif test_list[9] == 1: 
        scenario["time"]["hour"] = 18
        scenario["time"]["minute"] = 0
    elif test_list[9] == 2:
        scenario["time"]["hour"] = 0
        scenario["time"]["minute"] = 0
    else:
        print("time error") 

    # Set Weather    
    if "weather" not in scenario:
        scenario["weather"] = {
            "rain": 0,
            "fog": 0,
            "wetness": 0,
            "cloudiness": 0,
            "damage": 0
        }
    if test_list[10] == 0:
        scenario["weather"]["rain"] = 0
    elif test_list[10] == 1:
        scenario["weather"]["cloudiness"] = 1
    elif test_list[10] == 2:   
        scenario["weather"]["wetness"] = 1
    elif test_list[10] == 3:   
        scenario["weather"]["cloudiness"] = 0.5
        scenario["weather"]["wetness"] = 0.5
    elif test_list[10] == 4:     
        scenario["weather"]["rain"] = 0.33
    elif test_list[10] == 5:  
        scenario["weather"]["rain"] = 0.67
    elif test_list[10] == 6:
        scenario["weather"]["rain"] = 1
    else:
        print("weather error")

    # Set Target Speed
    if test_list[12] >= 0 & test_list[12] <= 5:
        max_speed = float(test_list[12]) * 10 / 3.6
        # max_speed = float(test_list[12]) / 3.6 / 10
        for agent in scenario["agents"]:
            if agent["type"] == 2:
                agent["behaviour"]["parameters"]["maxSpeed"] = max_speed
    else:
        print("speed error")

    # Save File
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, "temp.json")

    with open(file_path, 'w') as file:
        json.dump(scenario, file)
    scenario_class = dataparser.scenario.Scenario(_seed_path = file_path)

    return scenario_class
