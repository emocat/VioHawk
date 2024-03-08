import math
import copy
import dataparser

import lawbreaker_helper
from shapely.geometry import Polygon


def convert_to_template(scenario: dataparser.scenario.Scenario, map_info, session_name):
    result = {}
    agent_names = []

    result["ScenarioName"] = session_name
    result["MapVariable"] = ""
    result["map"] = "san_francisco"
    result["time"] = {
        "hour": scenario.elements["time"][0].hour,
        "minute": scenario.elements["time"][0].minute,
    }
    result["weather"] = {
        "rain": scenario.elements["weather"][0].rain,
        "sunny": scenario.elements["weather"][0].cloudiness,
        "wetness": scenario.elements["weather"][0].wetness,
        "fog": scenario.elements["weather"][0].fog,
    }

    ##### ego
    ego: dataparser.scenario.EgoVehicle = scenario.elements["ego"][0]
    ego_initial_position = map_info.get_position2(dict(x=ego.transform.position["x"], y=ego.transform.position["z"]))
    ego_destination_position = map_info.get_position2(dict(x=ego.destination.position["x"], y=ego.destination.position["z"]))
    result["ego"] = {
        "ID": "ego_vehicle",
        "name": "gt_sensors",
        "groundTruthPerception": True,
        "color": None,
        "start": {
            "lane_position": {
                "lane": ego_initial_position["lane"],
                "offset": ego_initial_position["offset"],
                "roadID": None,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": ego_initial_position["lane"],
                    "offset": ego_initial_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 0.0,
            },
            "speed": 0.0,
        },
        "destination": {
            "lane_position": {
                "lane": ego_destination_position["lane"],
                "offset": ego_destination_position["offset"],
                "roadID": None,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": ego_destination_position["lane"],
                    "offset": ego_destination_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 0.0,
            },
            "speed": 0.0,
        },
    }

    ##### npc
    npc_length = len(scenario.elements["npc"])
    result["npcList"] = []
    for npc_idx in range(npc_length):
        npc: dataparser.scenario.NPCVehicle = scenario.elements["npc"][npc_idx]
        npc_initial_position = map_info.get_position2(dict(x=npc.transform.position["x"], y=npc.transform.position["z"]))

        if npc.behaviour.name == "NPCLaneFollowBehaviour":
            npc_speed = npc.behaviour.maxSpeed
        else:
            raise Exception("Unknown NPC behaviour: {}".format(npc.behaviour.name))

        npc_dict = dict()
        npc_dict["ID"] = "npc" + str(npc_idx + 1)
        agent_names.append(npc_dict["ID"])
        npc_dict["name"] = "Sedan"
        npc_dict["color"] = None
        npc_dict["start"] = {
            "lane_position": {
                "lane": npc_initial_position["lane"],
                "offset": npc_initial_position["offset"],
                "roadID": None,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": npc_initial_position["lane"],
                    "offset": npc_initial_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 0.0,
            },
            "speed": npc_speed,
        }
        npc_dict["motion"] = []
        npc_dict["destination"] = None

        result["npcList"].append(npc_dict)

    ##### pedestrian
    pedestrian_length = len(scenario.elements["pedestrian"])
    result["pedestrianList"] = []
    for pedestrian_idx in range(pedestrian_length):
        pedestrian: dataparser.scenario.Pedestrian = scenario.elements["pedestrian"][pedestrian_idx]
        pedestrian_initial_position = map_info.get_position2(
            dict(
                x=pedestrian.transform.position["x"],
                y=pedestrian.transform.position["z"],
            )
        )
        pedestrian_destination_position = map_info.get_position2(
            dict(
                x=pedestrian.wayPoints[-1].position["x"],
                y=pedestrian.wayPoints[-1].position["z"],
            )
        )

        pedestrian_dict = dict()
        pedestrian_dict["ID"] = "ped" + str(pedestrian_idx)
        agent_names.append(pedestrian_dict["ID"])
        pedestrian_dict["name"] = "Bob"
        pedestrian_dict["start"] = {
            "position": {
                "x": pedestrian.transform.position["x"],
                "y": pedestrian.transform.position["z"],
                "z": 0,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": pedestrian_initial_position["lane"],
                    "offset": pedestrian_initial_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 90.0,
            },
            "speed": pedestrian.wayPoints[0].speed,
        }
        pedestrian_dict["motion"] = []
        pedestrian_dict["destination"] = {
            "position": {
                "x": pedestrian.wayPoints[-1].position["x"],
                "y": pedestrian.wayPoints[-1].position["z"],
                "z": 0,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": pedestrian_destination_position["lane"],
                    "offset": pedestrian_destination_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 90.0,
            },
            "speed": pedestrian.wayPoints[-1].speed,
        }
        pedestrian_dict["height"] = None
        pedestrian_dict["color"] = None
        pedestrian_dict["random_walk"] = False

        result["pedestrianList"].append(pedestrian_dict)

    ##### AgentNames
    result["obstacleList"] = []
    result["AgentNames"] = agent_names

    return result


def convert_to_output_trace(scenario: dataparser.scenario.Scenario, traces: list, map_info, session_name):
    result = {}
    agent_names = []

    result["ScenarioName"] = session_name
    result["MapVariable"] = ""
    result["map"] = "san_francisco"
    result["time"] = {
        "hour": scenario.elements["time"][0].hour,
        "minute": scenario.elements["time"][0].minute,
    }
    result["weather"] = {
        "rain": scenario.elements["weather"][0].rain,
        "sunny": scenario.elements["weather"][0].cloudiness,
        "wetness": scenario.elements["weather"][0].wetness,
        "fog": scenario.elements["weather"][0].fog,
    }

    ##### ego
    ego: dataparser.scenario.EgoVehicle = scenario.elements["ego"][0]
    ego_initial_position = map_info.get_position2(dict(x=ego.transform.position["x"], y=ego.transform.position["z"]))
    ego_destination_position = map_info.get_position2(dict(x=ego.destination.position["x"], y=ego.destination.position["z"]))
    result["ego"] = {
        "ID": "ego_vehicle",
        "name": "gt_sensors",
        "groundTruthPerception": True,
        "color": None,
        "start": {
            "lane_position": {
                "lane": ego_initial_position["lane"],
                "offset": ego_initial_position["offset"],
                "roadID": None,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": ego_initial_position["lane"],
                    "offset": ego_initial_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 0.0,
            },
            "speed": 0.0,
        },
        "destination": {
            "lane_position": {
                "lane": ego_destination_position["lane"],
                "offset": ego_destination_position["offset"],
                "roadID": None,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": ego_destination_position["lane"],
                    "offset": ego_destination_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 0.0,
            },
            "speed": 0.0,
        },
    }

    ##### npc
    npc_length = len(scenario.elements["npc"])
    result["npcList"] = []
    for npc_idx in range(npc_length):
        npc: dataparser.scenario.NPCVehicle = scenario.elements["npc"][npc_idx]
        npc_initial_position = map_info.get_position2(dict(x=npc.transform.position["x"], y=npc.transform.position["z"]))

        if npc.behaviour.name == "NPCLaneFollowBehaviour":
            npc_speed = npc.behaviour.maxSpeed
        else:
            raise Exception("Unknown NPC behaviour: {}".format(npc.behaviour.name))

        npc_dict = dict()
        npc_dict["ID"] = "npc" + str(npc_idx + 1)
        agent_names.append(npc_dict["ID"])
        npc_dict["name"] = "Sedan"
        npc_dict["color"] = None
        npc_dict["start"] = {
            "lane_position": {
                "lane": npc_initial_position["lane"],
                "offset": npc_initial_position["offset"],
                "roadID": None,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": npc_initial_position["lane"],
                    "offset": npc_initial_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 0.0,
            },
            "speed": npc_speed,
        }
        npc_dict["motion"] = []
        npc_dict["destination"] = None

        result["npcList"].append(npc_dict)

    ##### pedestrian
    pedestrian_length = len(scenario.elements["pedestrian"])
    result["pedestrianList"] = []
    for pedestrian_idx in range(pedestrian_length):
        pedestrian: dataparser.scenario.Pedestrian = scenario.elements["pedestrian"][pedestrian_idx]
        pedestrian_initial_position = map_info.get_position2(
            dict(
                x=pedestrian.transform.position["x"],
                y=pedestrian.transform.position["z"],
            )
        )
        pedestrian_destination_position = map_info.get_position2(
            dict(
                x=pedestrian.wayPoints[-1].position["x"],
                y=pedestrian.wayPoints[-1].position["z"],
            )
        )

        pedestrian_dict = dict()
        pedestrian_dict["ID"] = "ped" + str(pedestrian_idx)
        agent_names.append(pedestrian_dict["ID"])
        pedestrian_dict["name"] = "Bob"
        pedestrian_dict["start"] = {
            "position": {
                "x": pedestrian.transform.position["x"],
                "y": pedestrian.transform.position["z"],
                "z": 0,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": pedestrian_initial_position["lane"],
                    "offset": pedestrian_initial_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 90.0,
            },
            "speed": pedestrian.wayPoints[0].speed,
        }
        pedestrian_dict["motion"] = []
        pedestrian_dict["destination"] = {
            "position": {
                "x": pedestrian.wayPoints[-1].position["x"],
                "y": pedestrian.wayPoints[-1].position["z"],
                "z": 0,
            },
            "heading": {
                "ref_lane_point": {
                    "lane": pedestrian_destination_position["lane"],
                    "offset": pedestrian_destination_position["offset"],
                    "roadID": None,
                },
                "ref_angle": 90.0,
            },
            "speed": pedestrian.wayPoints[-1].speed,
        }
        pedestrian_dict["height"] = None
        pedestrian_dict["color"] = None
        pedestrian_dict["random_walk"] = False

        result["pedestrianList"].append(pedestrian_dict)

    ##### AgentNames
    result["obstacleList"] = []
    result["AgentNames"] = agent_names

    result["groundTruthPerception"] = True
    result["testFailures"] = {}
    result["testResult"] = "PASS"
    result["timeOfDay"] = result["time"]["hour"]
    result["minEgoObsDist"] = -1  # TODO
    result["destinationReached"] = True
    result["trace"] = []

    trace_time = len(traces)
    for t in range(trace_time):
        if t % 10 != 0:
            continue

        trace_data = traces[t]

        single_trace = dict()
        single_trace["timestamp"] = t

        # trace - ego
        trace_data_ego = trace_data["EGO"]
        single_trace_ego = dict()
        single_trace_ego["pose"] = dict()
        single_trace_ego["pose"]["position"] = dict(x=trace_data_ego["Position"]["x"], y=trace_data_ego["Position"]["z"], z=trace_data_ego["Position"]["y"])
        single_trace_ego["pose"]["orientation"] = trace_data_ego["Rotation"]
        single_trace_ego["pose"]["linearVelocity"] = trace_data_ego["LinearVelocity"]
        single_trace_ego["pose"]["linearAcceleration"] = trace_data_ego["Acceleration"]
        single_trace_ego["pose"]["angularVelocity"] = trace_data_ego["AngularVelocity"]
        single_trace_ego["pose"]["heading"] = math.radians(90 - trace_data_ego["Rotation"]["y"])
        # single_trace_ego["pose"]["heading"] = math.radians(trace_data_ego["Heading"])
        single_trace_ego["pose"]["linearAccelerationVrf"] = dict(x=0, y=0, z=0)
        single_trace_ego["pose"]["angularVelocityVrf"] = dict(x=0, y=0, z=0)
        single_trace_ego["pose"]["eulerAngles"] = dict(x=0, y=0, z=0)
        single_trace_ego["size"] = dict(length=trace_data_ego["Scale"]["z"], width=trace_data_ego["Scale"]["x"])
        single_trace_ego["Chasis"] = dict()
        single_trace_ego["Chasis"]["lowBeamOn"] = False  # TODO
        single_trace_ego["Chasis"]["highBeamOn"] = False  # TODO
        single_trace_ego["Chasis"]["turnSignal"] = False  # TODO
        single_trace_ego["Chasis"]["speed"] = trace_data_ego["LinearVelocity"]["x"]
        single_trace_ego["Chasis"]["hornOn"] = False  # TODO
        single_trace_ego["Chasis"]["engineOn"] = True  # TODO
        single_trace_ego["Chasis"]["gear"] = 1  # TODO
        single_trace_ego["Chasis"]["brake"] = 0  # TODO
        single_trace_ego["Chasis"]["day"] = scenario.elements["time"][0].day
        single_trace_ego["Chasis"]["hours"] = scenario.elements["time"][0].hour
        single_trace_ego["Chasis"]["minutes"] = scenario.elements["time"][0].minute
        single_trace_ego["Chasis"]["seconds"] = scenario.elements["time"][0].second
        single_trace_ego["Chasis"]["error_code"] = 0

        original_point = []
        original_point.append(single_trace_ego["pose"]["position"]["x"])
        original_point.append(single_trace_ego["pose"]["position"]["y"])
        heading_of_ego = single_trace_ego["pose"]["heading"]
        lengthen_of_ego = single_trace_ego["size"]["length"]
        width_of_ego = single_trace_ego["size"]["width"]

        ego_polygonPointList = []
        ego_polygonPointList = lawbreaker_helper.get_four_polygon_point_list_of_ego(original_point, heading_of_ego, lengthen_of_ego, width_of_ego)
        ego_position_area = Polygon(ego_polygonPointList)

        head_middle_point = lawbreaker_helper.get_the_head_middle_point_of_ego(original_point, heading_of_ego, lengthen_of_ego, width_of_ego)
        back_middle_point = lawbreaker_helper.get_the_back_middle_point_of_ego(original_point, heading_of_ego, lengthen_of_ego, width_of_ego)

        currentLane = lawbreaker_helper.check_current_lane(map_info, ego_position_area)
        single_trace_ego["currentLane"] = currentLane
        ahead_area_polygon = lawbreaker_helper.calculate_area_of_ahead(head_middle_point, single_trace_ego["pose"]["heading"], width_of_ego)
        back_area_polygon = lawbreaker_helper.calculate_area_of_ahead(back_middle_point, single_trace_ego["pose"]["heading"], width_of_ego)
        back_area_polygon2 = lawbreaker_helper.calculate_area_of_ahead2(back_middle_point, single_trace_ego["pose"]["heading"])

        ahead_area_polygon_for_opposite = lawbreaker_helper.calculate_area_of_ahead(head_middle_point, single_trace_ego["pose"]["heading"], width_of_ego, dist=30)

        left_area_polygon = lawbreaker_helper.calculate_area_of_ahead_left(back_middle_point, single_trace_ego["pose"]["heading"])
        right_area_polygon = lawbreaker_helper.calculate_area_of_ahead_right(back_middle_point, single_trace_ego["pose"]["heading"])
        backward_area_left = lawbreaker_helper.calculate_area_of_back_left(back_middle_point, single_trace_ego["pose"]["heading"], width_of_ego)
        backward_area_right = lawbreaker_helper.calculate_area_of_back_right(back_middle_point, single_trace_ego["pose"]["heading"], width_of_ego)

        crosswalkAhead = lawbreaker_helper.calculate_distance_to_crosswalk_ahead(map_info, ego_position_area, ahead_area_polygon)
        junctionAhead, junction_ahead_id = lawbreaker_helper.calculate_distance_to_junction_ahead(map_info, ego_position_area, ahead_area_polygon)
        stopSignAhead = lawbreaker_helper.calculate_distance_to_stopline_of_sign_ahead(map_info, ego_position_area, ahead_area_polygon)
        stoplineAhead = lawbreaker_helper.calculate_distance_to_stopline_of_ahead(map_info, ego_position_area, ahead_area_polygon)
        signalAhead = lawbreaker_helper.calculate_distance_to_signal_ahead(map_info, ego_position_area, ahead_area_polygon)

        trace_data_npcs = trace_data["NPCs"]
        isTrafficJam = lawbreaker_helper.check_is_traffic_jam(map_info, trace_data_npcs, junction_ahead_id)

        single_trace_ego["crosswalkAhead"] = crosswalkAhead
        single_trace_ego["junctionAhead"] = junctionAhead
        single_trace_ego["stopSignAhead"] = stopSignAhead
        single_trace_ego["stoplineAhead"] = stoplineAhead
        single_trace_ego["signalAhead"] = signalAhead  # FEATURE
        single_trace_ego["planning_of_turn"] = 0  # TODO: Planning.decision.vehicle_signal.turn_signal
        single_trace_ego["isTrafficJam"] = isTrafficJam
        single_trace_ego["isOverTaking"] = False
        single_trace_ego["isLaneChanging"] = False
        single_trace_ego["isTurningAround"] = False
        single_trace_ego["PriorityNPCAhead"] = False
        single_trace_ego["PriorityPedsAhead"] = False

        single_trace["ego"] = single_trace_ego

        # trace - truth
        single_trace_truth = dict()

        single_trace_truth_obsList = []
        for trace_data_npc in trace_data["NPCs"]:
            single_trace_truth_npc = dict()
            single_trace_truth_npc["id"] = trace_data_npc["Id"]
            single_trace_truth_npc["position"] = dict(x=trace_data_npc["Position"]["x"], y=trace_data_npc["Position"]["z"], z=trace_data_npc["Position"]["y"])
            # single_trace_truth_npc["theta"] = math.radians(trace_data_npc["Heading"])
            single_trace_truth_npc["theta"] = math.radians(90 - trace_data_npc["Rotation"]["y"])
            single_trace_truth_npc["velocity"] = trace_data_npc["Velocity"]
            single_trace_truth_npc["speed"] = trace_data_npc["LinearVelocity"]["x"]
            single_trace_truth_npc["length"] = trace_data_npc["Scale"]["y"]
            single_trace_truth_npc["width"] = trace_data_npc["Scale"]["x"]
            single_trace_truth_npc["height"] = trace_data_npc["Scale"]["z"]
            poly_list = lawbreaker_helper.get_four_polygon_point_list_of_ego([trace_data_npc["Position"]["x"], trace_data_npc["Position"]["z"]], single_trace_truth_npc["theta"], trace_data_npc["Scale"]["y"], trace_data_npc["Scale"]["x"])
            single_trace_truth_npc["polygonPointList"] = []
            for poly in poly_list:
                single_trace_truth_npc["polygonPointList"].append(dict(x=poly[0], y=poly[1], z=0))
            single_trace_truth_npc["trackingTime"] = 0
            if trace_data_npc["Label"] == "Pedestrian":
                single_trace_truth_npc["type"] = 3
            else:
                single_trace_truth_npc["type"] = 5
            single_trace_truth_npc["timestamp"] = single_trace["timestamp"]
            single_trace_truth_npc["pointCloudList"] = []
            single_trace_truth_npc["dropsList"] = []
            single_trace_truth_npc["acceleration"] = dict(x=0, y=0, z=0)
            single_trace_truth_npc["anchorPoint"] = single_trace_truth_npc["position"]
            single_trace_truth_npc["bbox2d"] = dict(xmin=0, ymin=0, xmax=0, ymax=0)
            single_trace_truth_npc["subType"] = 3
            single_trace_truth_npc["measurementsList"] = [{}]
            single_trace_truth_npc["measurementsList"][0]["sensorId"] = "velodyne128"
            single_trace_truth_npc["measurementsList"][0]["id"] = single_trace_truth_npc["id"]
            single_trace_truth_npc["measurementsList"][0]["position"] = single_trace_truth_npc["position"]
            single_trace_truth_npc["measurementsList"][0]["theta"] = single_trace_truth_npc["theta"]
            single_trace_truth_npc["measurementsList"][0]["length"] = single_trace_truth_npc["length"]
            single_trace_truth_npc["measurementsList"][0]["width"] = single_trace_truth_npc["width"]
            single_trace_truth_npc["measurementsList"][0]["height"] = single_trace_truth_npc["height"]
            single_trace_truth_npc["measurementsList"][0]["velocity"] = single_trace_truth_npc["velocity"]
            single_trace_truth_npc["measurementsList"][0]["type"] = single_trace_truth_npc["type"]
            single_trace_truth_npc["measurementsList"][0]["subType"] = single_trace_truth_npc["subType"]
            single_trace_truth_npc["measurementsList"][0]["timestamp"] = single_trace_truth_npc["timestamp"]
            single_trace_truth_npc["heightAboveGround"] = None
            single_trace_truth_npc["positionCovarianceList"] = []
            single_trace_truth_npc["velocityCovarianceList"] = []
            single_trace_truth_npc["accelerationCovarianceList"] = []
            single_trace_truth_npc["name"] = result["AgentNames"][single_trace_truth_npc["id"] - 2]
            single_trace_truth_npc["distToEgo"] = lawbreaker_helper.calculate_distToEgo(single_trace["ego"], single_trace_truth_npc)

            single_trace_truth_obsList.append(single_trace_truth_npc)

        if len(single_trace_truth_obsList) > 0:
            nearestGtObs = single_trace_truth_obsList[0]["name"]
            minDistToEgo = single_trace_truth_obsList[0]["distToEgo"]
            NearestNPC = None
            for _ii in single_trace_truth_obsList:
                if _ii["distToEgo"] <= minDistToEgo:
                    minDistToEgo = _ii["distToEgo"]
                    nearestGtObs = _ii["name"]
                    if _ii["type"] == 5:
                        NearestNPC = _ii["name"]
            single_trace_truth["minDistToEgo"] = minDistToEgo
            single_trace_truth["nearestGtObs"] = nearestGtObs
            single_trace_truth["NearestNPC"] = NearestNPC
            single_trace_truth["obsList"] = single_trace_truth_obsList
        else:
            single_trace_truth["obsList"] = single_trace_truth_obsList
            single_trace_truth["NearestNPC"] = None
            single_trace_truth["minDistToEgo"] = 200
            single_trace_truth["nearestGtObs"] = None

        single_trace_truth["NPCAhead"] = lawbreaker_helper.find_npc_ahead(map_info, single_trace_truth["obsList"], ego_position_area, ahead_area_polygon)
        single_trace_truth["PedAhead"] = lawbreaker_helper.find_ped_ahead(single_trace_truth["obsList"], ego_position_area, ahead_area_polygon)
        single_trace_truth["NPCOpposite"] = lawbreaker_helper.find_npc_opposite(single_trace_truth["obsList"], ego_position_area, single_trace_ego["pose"]["heading"], ahead_area_polygon_for_opposite)
        single_trace_truth["npcClassification"] = lawbreaker_helper.classify_oblist(map_info, single_trace["ego"], single_trace_truth_obsList)

        single_trace["truth"] = single_trace_truth

        # trace - traffic lights
        trace_traffic_lights = trace_data["Traffic_Lights"]
        single_trace["traffic_lights"] = {}
        if len(trace_traffic_lights) == 0:
            single_trace["traffic_lights"]["containLights"] = False
        else:
            single_trace["traffic_lights"]["containLights"] = True
            single_trace["traffic_lights"]["trafficLightList"] = []
            for traffic_light in trace_traffic_lights:
                if traffic_light["Label"] == "Unknown":
                    traffic_light_color = 0
                elif traffic_light["Label"] == "red":
                    traffic_light_color = 1
                elif traffic_light["Label"] == "yellow":
                    traffic_light_color = 2
                elif traffic_light["Label"] == "green":
                    traffic_light_color = 3
                else:
                    traffic_light_color = 0
                traffic_light_id = traffic_light["Id"]
                single_trace["traffic_lights"]["trafficLightList"].append(dict(id=traffic_light_id, color=traffic_light_color, blink=False))
            single_trace["traffic_lights"]["trafficLightStopLine"] = lawbreaker_helper.calculate_distance_to_traffic_light_stop_line(map_info, single_trace["ego"], traffic_light_id)

        result["trace"].append(single_trace)

        lawbreaker_helper.check_is_overtaking(map_info, result["trace"])
        lawbreaker_helper.check_is_lane_changing(map_info, result["trace"])
        lawbreaker_helper.check_is_TurningAround(map_info, result["trace"])
        lawbreaker_helper.Find_Priority_NPCs_and_Peds(map_info, result["trace"], back_area_polygon2, left_area_polygon, right_area_polygon, backward_area_left, backward_area_right)

    result["complete"] = True

    return result


def update_scenario_from_testcase(scenario: dataparser.scenario.Scenario, testcase: dict, map_info):
    new_scenario = copy.deepcopy(scenario)
    new_scenario.hash = None
    new_scenario.json_obj = None

    new_time = testcase["time"]
    new_scenario.elements["time"][0].hour = new_time["hour"]
    new_scenario.elements["time"][0].minute = new_time["minute"]

    new_weather = testcase["weather"]
    new_scenario.elements["weather"][0].rain = new_weather["rain"]
    new_scenario.elements["weather"][0].cloudiness = new_weather["sunny"]
    new_scenario.elements["weather"][0].wetness = new_weather["wetness"]
    new_scenario.elements["weather"][0].fog = new_weather["fog"]

    new_ego = testcase["ego"]
    new_ego_position = map_info.get_position([new_ego["start"]["lane_position"]["lane"], new_ego["start"]["lane_position"]["offset"]])
    new_point = dict(x=new_ego_position[0], y=new_scenario.elements["ego"][0].transform.position["y"], z=new_ego_position[1])
    new_point = lawbreaker_helper.find_the_point_on_line_for_lgsvl(new_point)
    new_scenario.elements["ego"][0].transform.position = new_point.position.to_json()
    new_scenario.elements["ego"][0].transform.rotation = new_point.rotation.to_json()
    print("[+] mutate ego position from {} -> {}".format(scenario.elements["ego"][0].transform.position, new_scenario.elements["ego"][0].transform.position))
    print("[+] mutate ego rotation from {} -> {}".format(scenario.elements["ego"][0].transform.rotation, new_scenario.elements["ego"][0].transform.rotation))

    new_ego_destination = testcase["ego"]["destination"]
    new_ego_destination_position = map_info.get_position([new_ego_destination["lane_position"]["lane"], new_ego_destination["lane_position"]["offset"]])
    new_point = dict(x=new_ego_destination_position[0], y=new_scenario.elements["ego"][0].destination.position["y"], z=new_ego_destination_position[1])
    new_point = lawbreaker_helper.find_the_point_on_line_for_lgsvl(new_point)
    new_scenario.elements["ego"][0].destination.position = new_point.position.to_json()
    new_scenario.elements["ego"][0].destination.rotation = new_point.rotation.to_json()
    print("[+] mutate ego destination position from {} -> {}".format(scenario.elements["ego"][0].destination.position, new_scenario.elements["ego"][0].destination.position))
    print("[+] mutate ego destination rotation from {} -> {}".format(scenario.elements["ego"][0].destination.rotation, new_scenario.elements["ego"][0].destination.rotation))

    new_npcs = testcase["npcList"]
    for npc_idx in range(len(new_npcs)):
        new_npc = new_npcs[npc_idx]
        new_npc_position = map_info.get_position([new_npc["start"]["lane_position"]["lane"], new_npc["start"]["lane_position"]["offset"]])
        new_point = dict(x=new_npc_position[0], y=new_scenario.elements["npc"][npc_idx].transform.position["y"], z=new_npc_position[1])
        new_point = lawbreaker_helper.find_the_point_on_line_for_lgsvl(new_point)
        new_scenario.elements["npc"][npc_idx].transform.position = new_point.position.to_json()
        new_scenario.elements["npc"][npc_idx].transform.rotation = new_point.rotation.to_json()
        print("[+] mutate npc {} position from {} -> {}".format(npc_idx, scenario.elements["npc"][npc_idx].transform.position, new_scenario.elements["npc"][npc_idx].transform.position))
        print("[+] mutate npc {} rotation from {} -> {}".format(npc_idx, scenario.elements["npc"][npc_idx].transform.rotation, new_scenario.elements["npc"][npc_idx].transform.rotation))

        new_speed = new_npc["start"]["speed"]
        if new_scenario.elements["npc"][npc_idx].behaviour.name == "NPCLaneFollowBehaviour":
            new_scenario.elements["npc"][npc_idx].behaviour.maxSpeed = new_speed
        else:
            raise Exception("Unknown NPC behaviour: {}".format(new_scenario.elements["npc"][npc_idx].behaviour.name))
        print("[+] mutate npc {} speed from {} -> {}".format(npc_idx, scenario.elements["npc"][npc_idx].behaviour.maxSpeed, new_scenario.elements["npc"][npc_idx].behaviour.maxSpeed))

    new_pedestrians = testcase["pedestrianList"]
    for pedestrian_idx in range(len(new_pedestrians)):
        new_pedestrian = new_pedestrians[pedestrian_idx]
        new_pedestrian_position = new_pedestrian["start"]["position"]
        new_point = dict(x=new_pedestrian_position["x"], y=new_pedestrian_position["z"], z=new_pedestrian_position["y"])
        new_point = lawbreaker_helper.find_the_point_on_line_for_lgsvl(new_point)
        new_scenario.elements["pedestrian"][pedestrian_idx].transform.position = new_point.position.to_json()
        new_scenario.elements["pedestrian"][pedestrian_idx].transform.rotation = new_point.rotation.to_json()
        print("[+] mutate pedestrian {} position from {} -> {}".format(pedestrian_idx, scenario.elements["pedestrian"][pedestrian_idx].transform.position, new_scenario.elements["pedestrian"][pedestrian_idx].transform.position))
        print("[+] mutate pedestrian {} rotation from {} -> {}".format(pedestrian_idx, scenario.elements["pedestrian"][pedestrian_idx].transform.rotation, new_scenario.elements["pedestrian"][pedestrian_idx].transform.rotation))

        new_pedestrian_speed = new_pedestrian["start"]["speed"]
        new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[0].speed = new_pedestrian_speed
        print("[+] mutate pedestrian {} speed from {} -> {}".format(pedestrian_idx, scenario.elements["pedestrian"][pedestrian_idx].wayPoints[0].speed, new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[0].speed))

        new_pedestrian_destination = new_pedestrian["destination"]
        new_pedestrian_destination_position = new_pedestrian_destination["position"]
        new_point = dict(x=new_pedestrian_destination_position["x"], y=new_pedestrian_destination_position["z"], z=new_pedestrian_destination_position["y"])
        new_point = lawbreaker_helper.find_the_point_on_line_for_lgsvl(new_point)
        new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].position = new_point.position.to_json()
        new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].angle = new_point.rotation.to_json()
        print("[+] mutate pedestrian {} destination position from {} -> {}".format(pedestrian_idx, scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].position, new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].position))
        print("[+] mutate pedestrian {} destination rotation from {} -> {}".format(pedestrian_idx, scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].angle, new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].angle))

        new_pedestrian_destination_speed = new_pedestrian_destination["speed"]
        new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].speed = new_pedestrian_destination_speed
        print("[+] mutate pedestrian {} destination speed from {} -> {}".format(pedestrian_idx, scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].speed, new_scenario.elements["pedestrian"][pedestrian_idx].wayPoints[-1].speed))

    return new_scenario
