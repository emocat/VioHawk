import math
import lgsvl
import numpy as np
from shapely.geometry import Polygon, LineString, Point


def viohawk_get_four_wheel_position(position: dict, rotation: dict) -> list:
    wheel = []
    length = 2.835 / 2
    width = 1.66 / 2
    l2 = length * length + width * width
    l = np.sqrt(l2)
    sina = width / l
    if isinstance(position, lgsvl.Vector):
        position = {"x": position.x, "z": position.z}
        rotation = {"y": rotation.y}
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
    w4_x = l * np.sin(b + math.pi + a) + x
    w4_y = l * np.cos(b + math.pi + a) + y
    wheel.append([w4_x, w4_y])
    w3_x = l * np.sin(b + math.pi - a) + x
    w3_y = l * np.cos(b + math.pi - a) + y
    wheel.append([w3_x, w3_y])
    # w4_x = l * np.sin(b + math.pi + a) + x
    # w4_y = l * np.cos(b + math.pi + a) + y
    # wheel.append([w4_x, w4_y])

    return wheel


def viohawk_get_ego_polygon(position: dict, rotation: dict) -> Polygon:
    ego_wheel = viohawk_get_four_wheel_position(position, rotation)
    ego_polygon = Polygon(ego_wheel)
    return ego_polygon


def get_four_polygon_point_list_of_ego(original_point, heading_of_ego, lengthen_of_ego, width_of_ego):
    # zhouju = 2.71
    zhouju = 2.697298

    result = []

    point0 = []
    point0.append(original_point[0] + (lengthen_of_ego - zhouju) / 2 + zhouju)
    point0.append(original_point[1] + width_of_ego / 2)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    result.append(point0)

    point1 = []
    point1.append(original_point[0] + (lengthen_of_ego - zhouju) / 2 + zhouju)
    point1.append(original_point[1] - width_of_ego / 2)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    result.append(point1)

    point2 = []
    point2.append(original_point[0] - (lengthen_of_ego - zhouju) / 2)
    point2.append(original_point[1] - width_of_ego / 2)
    x = point2[0]
    y = point2[1]
    point2 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    result.append(point2)

    point3 = []
    point3.append(original_point[0] - (lengthen_of_ego - zhouju) / 2)
    point3.append(original_point[1] + width_of_ego / 2)
    x = point3[0]
    y = point3[1]
    point3 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    result.append(point3)

    return result


def get_the_back_middle_point_of_ego(original_point, heading_of_ego, lengthen_of_ego, width_of_ego):
    # zhouju = 2.71
    zhouju = 2.697298
    result = []

    point0 = []
    point0.append(original_point[0] - (lengthen_of_ego - zhouju) / 2)
    point0.append(original_point[1] - width_of_ego / 2)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])

    point1 = []
    point1.append(original_point[0] - (lengthen_of_ego - zhouju) / 2)
    point1.append(original_point[1] + width_of_ego / 2)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])

    result.append((point0[0] + point1[0]) / 2)
    result.append((point0[1] + point1[1]) / 2)
    return result


def get_the_head_middle_point_of_ego(original_point, heading_of_ego, lengthen_of_ego, width_of_ego):
    # zhouju = 2.71
    zhouju = 2.697298
    result = []

    point0 = []
    point0.append(original_point[0] + (lengthen_of_ego - zhouju) / 2 + zhouju)
    point0.append(original_point[1] + width_of_ego / 2)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])

    point1 = []
    point1.append(original_point[0] + (lengthen_of_ego - zhouju) / 2 + zhouju)
    point1.append(original_point[1] - width_of_ego / 2)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])

    result.append((point0[0] + point1[0]) / 2)
    result.append((point0[1] + point1[1]) / 2)
    return result


def check_current_lane(map_info, ego):
    value = {}

    result = map_info.find_which_area_the_ego_is_in(ego)

    if result != None:
        if result[0].__contains__("lane_id"):
            ego_lane_id = result[0]["lane_id"]
            value["currentLaneId"] = ego_lane_id
            forward = 0
            left = 0
            right = 0
            U = 0
            number = 0
            for _i in result:
                number += _i["laneNumber"]
                if _i["turn"] == 1:
                    forward = 1
                elif _i["turn"] == 2:
                    left = 1
                elif _i["turn"] == 3:
                    right = 1
                elif _i["turn"] == 4:
                    U = 1
            if forward == 1:
                if left == 1:
                    if right == 1:
                        # value["turn"] = "forwardOrLeftOrRight"
                        value["turn"] = 6
                    else:
                        # value["turn"] = "forwardOrLeft"
                        value["turn"] = 4
                else:
                    if right == 1:
                        # value["turn"] = "forwardOrRight"
                        value["turn"] = 5
                    else:
                        # value["turn"] = "forward"
                        value["turn"] = 0
            else:
                if left == 1:
                    if right == 1:
                        # value["turn"] = "LeftOrRight"
                        value["turn"] = 7
                    else:
                        # value["turn"] = "Left"
                        value["turn"] = 1
                else:
                    if right == 1:
                        # value["turn"] = "Right"
                        value["turn"] = 2
                    else:
                        if U == 1:
                            # value["turn"] = "UTurn"
                            value["turn"] = 3
                        else:
                            print("Unexpected!!!")
            value["number"] = number
        if result[0].__contains__("junction_id"):
            ego_lane_id = result[0]["junction_id"]
            value["currentLaneId"] = None
            value["number"] = 0
    else:
        ego_lane_id = None

    return value


def add_heading_to_ego(angle, x, y, pointx, pointy):
    angle = -angle
    srx = (x - pointx) * math.cos(angle) + (y - pointy) * math.sin(angle) + pointx

    sry = (y - pointy) * math.cos(angle) - (x - pointx) * math.sin(angle) + pointy

    point = [srx, sry]

    return point


def calculate_area_of_ahead(original_point, heading_of_ego, width_of_ego, dist=200):
    # calculate the Ahead area
    ahead_area = []
    point0 = []
    point0.append(original_point[0] + dist)
    point0.append(original_point[1] + dist)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point0)

    point1 = []
    point1.append(original_point[0] + dist)
    point1.append(original_point[1] - dist)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point1)

    point2 = []
    point2.append(original_point[0] - 0)
    point2.append(original_point[1] - width_of_ego / 2)
    x = point2[0]
    y = point2[1]
    point2 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point2)

    point3 = []
    point3.append(original_point[0] - 0)
    point3.append(original_point[1] + width_of_ego / 2)
    x = point3[0]
    y = point3[1]
    point3 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point3)

    ahead_area_polygon = Polygon(ahead_area)
    return ahead_area_polygon


def calculate_area_of_ahead2(original_point, heading_of_ego):
    # calculate the Ahead area
    ahead_area = []
    point0 = []
    point0.append(original_point[0] + 200)
    point0.append(original_point[1] + 200)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point0)

    point1 = []
    point1.append(original_point[0] + 200)
    point1.append(original_point[1] - 200)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point1)

    point2 = []
    point2.append(original_point[0] - 0)
    point2.append(original_point[1] - 200)
    x = point2[0]
    y = point2[1]
    point2 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point2)

    point3 = []
    point3.append(original_point[0] - 0)
    point3.append(original_point[1] + 200)
    x = point3[0]
    y = point3[1]
    point3 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point3)

    ahead_area_polygon = Polygon(ahead_area)
    return ahead_area_polygon


def calculate_area_of_ahead_left(original_point, heading_of_ego):
    # calculate the Ahead area
    ahead_area = []
    point0 = []
    point0.append(original_point[0] + 30)
    point0.append(original_point[1] + 0)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point0)

    point1 = []
    point1.append(original_point[0] + 30)
    point1.append(original_point[1] - 30)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point1)

    point2 = []
    point2.append(original_point[0] - 0)
    point2.append(original_point[1] - 30)
    x = point2[0]
    y = point2[1]
    point2 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point2)

    point3 = []
    point3.append(original_point[0] - 0)
    point3.append(original_point[1] + 0)
    x = point3[0]
    y = point3[1]
    point3 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point3)

    ahead_area_polygon = Polygon(ahead_area)
    return ahead_area_polygon


def calculate_area_of_ahead_right(original_point, heading_of_ego):
    # calculate the Ahead area
    ahead_area = []
    point0 = []
    point0.append(original_point[0] + 30)
    point0.append(original_point[1] + 30)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point0)

    point1 = []
    point1.append(original_point[0] + 30)
    point1.append(original_point[1] - 0)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point1)

    point2 = []
    point2.append(original_point[0] - 0)
    point2.append(original_point[1] - 0)
    x = point2[0]
    y = point2[1]
    point2 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point2)

    point3 = []
    point3.append(original_point[0] - 0)
    point3.append(original_point[1] + 30)
    x = point3[0]
    y = point3[1]
    point3 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point3)

    ahead_area_polygon = Polygon(ahead_area)
    return ahead_area_polygon


def calculate_area_of_back_left(original_point, heading_of_ego, width_of_ego):
    # calculate the Ahead area
    ahead_area = []
    point0 = []
    point0.append(original_point[0] + 0)
    point0.append(original_point[1] - width_of_ego / 2 - 0.3)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point0)

    point1 = []
    point1.append(original_point[0] + 0)
    point1.append(original_point[1] - width_of_ego / 2 - 0.3 - 3)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point1)

    point2 = []
    point2.append(original_point[0] - 30)
    point2.append(original_point[1] - width_of_ego / 2 - 0.3 - 3)
    x = point2[0]
    y = point2[1]
    point2 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point2)

    point3 = []
    point3.append(original_point[0] - 30)
    point3.append(original_point[1] - width_of_ego / 2 - 0.3)
    x = point3[0]
    y = point3[1]
    point3 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point3)

    ahead_area_polygon = Polygon(ahead_area)
    return ahead_area_polygon


def calculate_area_of_back_right(original_point, heading_of_ego, width_of_ego):
    # calculate the Ahead area
    ahead_area = []
    point0 = []
    point0.append(original_point[0] + 0)
    point0.append(original_point[1] + width_of_ego / 2 + 0.3 + 3)
    x = point0[0]
    y = point0[1]
    point0 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point0)

    point1 = []
    point1.append(original_point[0] + 0)
    point1.append(original_point[1] + width_of_ego / 2 + 0.3)
    x = point1[0]
    y = point1[1]
    point1 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point1)

    point2 = []
    point2.append(original_point[0] - 30)
    point2.append(original_point[1] + width_of_ego / 2 + 0.3)
    x = point2[0]
    y = point2[1]
    point2 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point2)

    point3 = []
    point3.append(original_point[0] - 30)
    point3.append(original_point[1] + width_of_ego / 2 + 0.3 + 3)
    x = point3[0]
    y = point3[1]
    point3 = add_heading_to_ego(heading_of_ego, x, y, original_point[0], original_point[1])
    ahead_area.append(point3)

    ahead_area_polygon = Polygon(ahead_area)
    return ahead_area_polygon


def calculate_distance_to_crosswalk_ahead(map_info, ego_polygon, ahead_area_polygon):
    result = []
    crosswalk_list = map_info.get_crosswalk_config()
    ego = ego_polygon

    for key in crosswalk_list:
        points = []
        points = crosswalk_list[key]
        the_area = Polygon(points)
        if ahead_area_polygon.distance(the_area) == 0:
            result.append(ego.distance(the_area))

    if result != []:
        _min = result[0]
    else:
        _min = 200
    for _i in result:
        if _min > _i:
            _min = _i
    return _min


def calculate_distance_to_junction_ahead(map_info, ego_polygon, ahead_area_polygon):
    result = {}
    junction_list = map_info.areas["junction_areas"]
    ego = ego_polygon

    for key in junction_list:
        points = []
        points = junction_list[key]
        the_area = Polygon(points)
        if ahead_area_polygon.distance(the_area) == 0:
            dist = ego.distance(the_area)
            result[key] = dist

    junction_ahead = None
    _min = 200
    for key in result:
        if _min > result[key]:
            _min = result[key]
            junction_ahead = key
    return _min, junction_ahead


def calculate_distance_to_signal_ahead(map_info, ego_polygon, ahead_area_polygon):
    result = []
    traffic_signal_list = map_info.get_traffic_signals()
    ego = ego_polygon

    for _i in traffic_signal_list:
        points = _i["point"]
        the_point = Point(points["x"], points["z"])
        if ahead_area_polygon.distance(the_point) == 0:
            result.append(ego.distance(the_point))

    if result != []:
        _min = result[0]
    else:
        _min = 200
    for _i in result:
        if _min > _i:
            _min = _i
    return _min


def calculate_distance_to_stopline_of_sign_ahead(map_info, ego_polygon, ahead_area_polygon):
    result = []
    traffic_sign_list = map_info.get_traffic_sign()

    ego = ego_polygon

    for _i in traffic_sign_list:
        # single_result = {}
        # single_result["id"] = _i["id"]
        # single_result["type"] = _i["type"]
        points = []
        for _j in _i["stop_line_points"]:
            temp = []
            temp.append(_j["x"])
            temp.append(_j["y"])
            points.append(temp)
        the_line = LineString(points)
        if ahead_area_polygon.distance(the_line) == 0:
            result.append(ego.distance(the_line))

    if result != []:
        _min = result[0]
    else:
        _min = 200
    for _i in result:
        if _min > _i:
            _min = _i
    return _min


def calculate_distance_to_stopline_of_ahead(map_info, ego_polygon, ahead_area_polygon):
    min1 = calculate_distance_to_stopline_of_sign_ahead(map_info, ego_polygon, ahead_area_polygon)

    result = []
    traffic_signal_list = map_info.get_traffic_signals()
    ego = ego_polygon

    for _i in traffic_signal_list:
        points = []
        for _j in _i["stop_line_points"]:
            temp = []
            temp.append(_j["x"])
            temp.append(_j["z"])
            points.append(temp)
        the_line = LineString(points)
        if ahead_area_polygon.distance(the_line) == 0:
            result.append(ego.distance(the_line))

    if result != []:
        _min = result[0]
    else:
        _min = 200
    for _i in result:
        if _min > _i:
            _min = _i

    if _min < min1:
        return _min
    else:
        return min1


def calculate_distance_to_traffic_light_stop_line(map_info, Ego, ID):
    # result = []
    traffic_signal_list = map_info.get_traffic_signals()

    original_point = []
    original_point.append(Ego["pose"]["position"]["x"])
    original_point.append(Ego["pose"]["position"]["y"])
    heading_of_ego = Ego["pose"]["heading"]
    lengthen_of_ego = Ego["size"]["length"]
    width_of_ego = Ego["size"]["width"]
    ego_polygonPointList = []
    ego_polygonPointList = get_four_polygon_point_list_of_ego(
        original_point, heading_of_ego, lengthen_of_ego, width_of_ego
    )
    ego = Polygon(ego_polygonPointList)
    # point = Point(position["x"], position["y"])

    _distance = 10000000
    single_result = {}
    for _i in traffic_signal_list:
        if _i["id"] == ID:
            single_result["id"] = _i["id"]
            single_result["types"] = _i["sub_signal_type_list"]

            points = []
            for _j in _i["stop_line_points"]:
                temp = []
                temp.append(_j["x"])
                temp.append(_j["y"])
                points.append(temp)
            the_line = LineString(points)

            single_result["distance"] = ego.distance(the_line)
        else:
            # single_result = {}
            # single_result["id"] = _i["id"]
            # single_result["types"] = _i["sub_signal_type_list"]

            points = []
            for _j in _i["stop_line_points"]:
                temp = []
                temp.append(_j["x"])
                temp.append(_j["y"])
                points.append(temp)
            the_line = LineString(points)

            distance_of_temp = ego.distance(the_line)
            if distance_of_temp < _distance:
                _distance = distance_of_temp

            if hasattr(single_result, "distance"):
                if single_result["distance"] > _distance:
                    print("Traffic Light Error: wrong traffic light perception!")
                else:
                    pass
            # pass
        # result.append(single_result)
    return single_result["distance"]


def check_is_traffic_jam(map_info, oblist, junction_ahead):
    number = 0
    for _i in oblist:
        if _i["LinearVelocity"]["x"] < 1 and _i["Label"] != "Pedestrian":
            poly = viohawk_get_ego_polygon(_i["Position"], _i["Rotation"])
            junction = map_info.check_whether_in_junction_area(poly)
            if junction != []:
                # print(junction)
                # print(self.junction_ahead)
                if junction[0]["junction_id"] == junction_ahead:
                    number = number + 1

    if number >= 3:
        return True
    else:
        return False


def check_is_overtaking(map_info, trace):
    # trace[-1]["ego"]["isOverTaking"] = is_overtaking    # Planning.decision.object_decision
    # if is_overtaking:
    #     trace[-1]["ego"]["isLaneChanging"] = True
    # else:
    #     trace[-1]["ego"]["isLaneChanging"] = False
    trace[-1]["ego"]["isLaneChanging"] = False


def check_is_lane_changing(map_info, trace):
    num_of_track = -10  # check the value of 5 states before
    if len(trace) >= -num_of_track:
        if trace[num_of_track]["ego"]["isLaneChanging"] == False:
            previous_trace = trace[num_of_track]
            orig = previous_trace["ego"]["currentLane"]["currentLaneId"]
            # if previous_trace["ego"]["planning_of_turn"] != 0:
            for num in range(num_of_track + 1, 0):
                dest = trace[num]["ego"]["currentLane"]["currentLaneId"]
                In_the_same_road = map_info.check_whether_two_lanes_are_in_the_same_road(orig, dest)
                if dest != orig and dest != None and In_the_same_road == True:
                    trace[num_of_track]["ego"]["isLaneChanging"] = True


def process_with_angle_pi(angle_pi):
    if angle_pi < 0:
        return angle_pi + 2 * math.pi
    else:
        return angle_pi


def check_is_TurningAround(map_info, trace):
    num_of_track = -20
    if len(trace) >= -num_of_track:
        trace[num_of_track]["ego"]["isTurningAround"] = False
        previous_trace = trace[num_of_track]
        # orig = previous_trace["ego"]["currentLane"]["currentLaneId"]
        orig = previous_trace["ego"]["pose"]["heading"]
        orig = process_with_angle_pi(orig)
        if previous_trace["ego"]["planning_of_turn"] != 0:
            # print("is turning")
            for num in range(num_of_track + 1, 0):
                # dest = self.trace[num]["ego"]["currentLane"]["currentLaneId"]
                dest = trace[num]["ego"]["pose"]["heading"]
                dest = process_with_angle_pi(dest)
                # print(str(dest) +"-" + str(orig) +"= "+str(abs(dest - orig)))
                if abs(dest - orig) > 3 * math.pi / 4:
                    trace[num_of_track]["ego"]["isTurningAround"] = True
                    # print("dectect Turning Around previous!!")


def convert_velocity_to_speed(velocity):
    x = velocity["x"]
    y = velocity["y"]
    z = velocity["z"]

    return math.sqrt(x * x + y * y + z * z)


def Find_Priority_NPCs_and_Peds(
    map_info, trace, ahead_square_area, left_area_polygon, right_area_polygon, backward_area_left, backward_area_right
):
    num_of_track = -1
    if len(trace) >= -num_of_track:
        _sub_Find_Priority_NPCs_and_Peds(
            map_info,
            trace,
            ahead_square_area,
            left_area_polygon,
            right_area_polygon,
            num_of_track,
            backward_area_left,
            backward_area_right,
        )


def _sub_Find_Priority_NPCs_and_Peds(
    map_info,
    trace,
    ahead_square_area,
    left_area_polygon,
    right_area_polygon,
    num_of_track,
    backward_area_left,
    backward_area_right,
):
    previous_trace = trace[num_of_track]
    previous_trace["ego"]["PriorityNPCAhead"] = False
    previous_trace["ego"]["PriorityPedsAhead"] = False

    obstacles = previous_trace["truth"]["obsList"]
    _road = previous_trace["truth"]

    heading_of_ego = previous_trace["ego"]["pose"]["heading"]
    heading_of_ego = process_with_angle_pi(heading_of_ego)

    # if we are turning, we should give way to the cars in the direct way
    for obstacle in obstacles:
        points = []
        for _p in obstacle["polygonPointList"]:
            x = _p["x"]
            y = _p["y"]
            points.append((x, y))
        the_area = Polygon(points)
        # Find priority NPC of ahead
        if _road["NPCAhead"] == obstacle["name"] and obstacle["distToEgo"] < 3:
            previous_trace["ego"]["PriorityNPCAhead"] = True
        if obstacle["type"] == 5:
            # Find priority NPC when turning
            heading_of_npc = obstacle["theta"]
            heading_of_npc = process_with_angle_pi(heading_of_npc)
            if previous_trace["ego"]["planning_of_turn"] != 0 and previous_trace["ego"]["isLaneChanging"] == False:
                points = []
                if (
                    abs(heading_of_npc - heading_of_ego) > math.pi / 4
                    and abs(heading_of_npc - heading_of_ego) < 3 * math.pi / 4
                ):
                    if obstacle["distToEgo"] < 30 and ahead_square_area.distance(the_area) == 0:
                        previous_trace["ego"]["PriorityNPCAhead"] = True
                        # print("Find priority NPC for turing!")
            # Find priority NPC when lane changing
            if previous_trace["ego"]["isLaneChanging"] == True:
                if abs(heading_of_npc - heading_of_ego) < math.pi / 4:
                    ego_speed = convert_velocity_to_speed(previous_trace["ego"]["pose"]["linearVelocity"])
                    if (
                        previous_trace["ego"]["planning_of_turn"] == 1 and backward_area_left.distance(the_area) == 0
                    ):  # left lane changing
                        if obstacle["distToEgo"] < 10 and obstacle["speed"] > ego_speed:
                            previous_trace["ego"]["PriorityNPCAhead"] = True
                            print("Find priority NPC for left lane changing!")
                    if (
                        previous_trace["ego"]["planning_of_turn"] == 2 and backward_area_right.distance(the_area) == 0
                    ):  # right lane changing
                        if obstacle["distToEgo"] < 10 and obstacle["speed"] > ego_speed:
                            previous_trace["ego"]["PriorityNPCAhead"] = True
                            print("Find priority NPC for right lane changing!")

        elif obstacle["type"] == 3:
            if previous_trace["ego"]["planning_of_turn"] == 0:
                if obstacle["distToEgo"] < 3 and ahead_square_area.distance(the_area) == 0:
                    previous_trace["ego"]["PriorityPedsAhead"] = True
                    print("Find priority Ped for direct!")
            if previous_trace["ego"]["planning_of_turn"] == 1:
                if obstacle["distToEgo"] < 10 and left_area_polygon.distance(the_area) == 0:
                    previous_trace["ego"]["PriorityPedsAhead"] = True
                    print("Find priority Ped for turning left!")
            if previous_trace["ego"]["planning_of_turn"] == 2:
                if obstacle["distToEgo"] < 10 and right_area_polygon.distance(the_area) == 0:
                    previous_trace["ego"]["PriorityPedsAhead"] = True
                    print("Find priority Ped for turning right!")

            junction_list = map_info.areas["junction_areas"]
            for key in junction_list:
                points = junction_list[key]
                junction_area = Polygon(points)
                if the_area.distance(junction_area) == 0:
                    previous_trace["ego"]["PriorityPedsAhead"] = True


def find_npc_ahead(map_info, oblist, ego_polygon, ahead_area_polygon):
    ego = ego_polygon

    return_value = None

    result = map_info.find_which_area_the_ego_is_in(ego)
    if result != None:
        if result[0].__contains__("lane_id"):  # If in lane area, get the name of the lane.
            ego_lane_id = result[0]["lane_id"]
            _temp = {}
            for _i in oblist:
                points = []
                for _p in _i["polygonPointList"]:
                    x = _p["x"]
                    y = _p["y"]
                    points.append((x, y))
                the_area = Polygon(points)
                result1 = map_info.find_which_area_the_ego_is_in(the_area)
                # if ahead_area_polygon.distance(the_area) == 0 and _i["type"] == 5 and result1 == result:
                if (
                    ahead_area_polygon.distance(the_area) == 0 and _i["type"] == 5
                ):  # for car which is ahead but not in same lane (specific rules)
                    _temp[_i["name"]] = ego.distance(the_area)
                    return_value = _i["name"]
            for key in _temp:
                if _temp[key] < _temp[return_value]:
                    return_value = key
            return return_value
        else:
            ego_lane_id = result[0]["junction_id"]  # If in junction area, get the name of the lane.
            _temp = {}
            for _i in oblist:
                points = []
                for _p in _i["polygonPointList"]:
                    x = _p["x"]
                    y = _p["y"]
                    points.append((x, y))
                the_area = Polygon(points)
                if ahead_area_polygon.distance(the_area) == 0 and _i["type"] == 5:
                    _temp[_i["name"]] = ego.distance(the_area)
                    return_value = _i["name"]
            for key in _temp:
                if _temp[key] < _temp[return_value]:
                    return_value = key
            return return_value
    else:
        print("!bug of localization of ego")
        return return_value


def find_ped_ahead(oblist, ego_polygon, ahead_area_polygon):
    ego = ego_polygon

    return_value = None
    _temp = {}
    for _i in oblist:
        points = []
        for _p in _i["polygonPointList"]:
            x = _p["x"]
            y = _p["y"]
            points.append((x, y))
        the_area = Polygon(points)
        if ahead_area_polygon.distance(the_area) == 0 and _i["type"] == 3:
            _temp[_i["name"]] = ego.distance(the_area)
            return_value = _i["name"]
    for key in _temp:
        if _temp[key] < _temp[return_value]:
            return_value = key
    return return_value


def find_npc_opposite(oblist, ego_polygon, heading, ahead_area_polygon):
    ego = ego_polygon

    heading_of_ego = heading

    return_value = None
    _temp = {}
    for _i in oblist:
        points = []
        for _p in _i["polygonPointList"]:
            x = _p["x"]
            y = _p["y"]
            points.append((x, y))
        the_area = Polygon(points)
        if ahead_area_polygon.distance(the_area) == 0 and _i["type"] == 5:
            heading_of_npc = _i["theta"]
            heading_of_npc = process_with_angle_pi(heading_of_npc)
            if (
                abs(heading_of_npc - heading_of_ego) > 3 * math.pi / 4
                and abs(heading_of_npc - heading_of_ego) < 5 * math.pi / 4
            ):
                _temp[_i["name"]] = ego.distance(the_area)
                return_value = _i["name"]
    for key in _temp:
        if _temp[key] < _temp[return_value]:
            return_value = key
    return return_value


def find_the_point_on_line_for_lgsvl(point):
    sim = lgsvl.Simulator(lgsvl.wise.SimulatorSettings.simulator_host, lgsvl.wise.SimulatorSettings.simulator_port)
    sx = point["x"]
    sy = point["y"]
    sz = point["z"]
    adjusted_point = lgsvl.Vector(sx, sy, sz)
    new_point = sim.map_point_on_lane(adjusted_point)
    sim.reset()
    sim.close()

    return new_point


def calculate_distToEgo(Ego, obstacle):
    original_point = []
    original_point.append(Ego["pose"]["position"]["x"])
    original_point.append(Ego["pose"]["position"]["y"])
    # original_point.append(self.Ego["pose"]["position"]["z"])

    heading_of_ego = Ego["pose"]["heading"]

    lengthen_of_ego = Ego["size"]["length"]
    width_of_ego = Ego["size"]["width"]

    ego_polygonPointList = []

    ego_polygonPointList = get_four_polygon_point_list_of_ego(
        original_point, heading_of_ego, lengthen_of_ego, width_of_ego
    )

    obstacles_polygonPointList = []

    for _i in obstacle["polygonPointList"]:
        temp = []
        temp.append(_i["x"])
        temp.append(_i["y"])
        obstacles_polygonPointList.append(temp)

    ego = Polygon(ego_polygonPointList)

    obstacle = Polygon(obstacles_polygonPointList)

    Mindis = ego.distance(obstacle)

    return Mindis


def classify_oblist(map_info, Ego, oblist):
    x = Ego["pose"]["position"]["x"]
    y = Ego["pose"]["position"]["y"]
    point = (x, y)
    the_result_after_classification = dict()

    result = map_info.find_which_area_the_point_is_in(point)
    if result != None:
        if result[0].__contains__("lane_id"):
            ego_lane_id = result[0]["lane_id"]
        else:
            ego_lane_id = result[0]["junction_id"]
    else:
        ego_lane_id = None

    same_list = []
    different_list = []
    junction_list = []

    fourth_list = []
    fivth_list = []
    unknown_list = []
    for ob in oblist:
        temp = dict()
        x = ob["position"]["x"]
        y = ob["position"]["y"]
        point = (x, y)
        result = map_info.find_which_area_the_point_is_in(point)
        if result != None:
            if result[0].__contains__("lane_id"):
                oblist_lane_id = result[0]["lane_id"]
            else:
                oblist_lane_id = result[0]["junction_id"]
        else:
            oblist_lane_id = None
        if ego_lane_id != None and oblist_lane_id != None:
            if "lane" in ego_lane_id:
                # print('???')
                if "lane" in oblist_lane_id:
                    if map_info.check_whether_two_lanes_are_in_the_same_road(ego_lane_id, oblist_lane_id):
                        # print("ego and "+ob["name"] +" on the same Road")
                        temp["name"] = ob["name"]
                        temp["laneId"] = oblist_lane_id
                        temp["turn"] = result[0]["turn"]
                        same_list.append(temp)
                    else:
                        # print("ego and "+ob["name"] +" on the different Road")
                        temp["name"] = ob["name"]
                        temp["laneId"] = oblist_lane_id
                        temp["turn"] = result[0]["turn"]
                        different_list.append(temp)
                elif "J_" in oblist_lane_id or "junction" in oblist_lane_id:
                    # print("ego on lane and "+ob["name"] +" on the junction")
                    temp["name"] = ob["name"]
                    temp["junctionId"] = oblist_lane_id
                    junction_list.append(temp)
            elif "J_" in ego_lane_id or "junction" in oblist_lane_id:
                # print('!!!!')
                if "lane" in oblist_lane_id:
                    temp["name"] = ob["name"]
                    temp["laneId"] = oblist_lane_id
                    temp["turn"] = result[0]["turn"]
                    fourth_list.append(temp)
                elif "J_" in ego_lane_id or "junction" in oblist_lane_id:
                    temp["name"] = ob["name"]
                    temp["junctionId"] = oblist_lane_id
                    fivth_list.append(temp)
        else:
            temp["name"] = ob["name"]
            unknown_list.append(temp)

    # When ego on lane
    the_result_after_classification["NextToEgo"] = same_list
    the_result_after_classification["OntheDifferentRoad"] = different_list
    the_result_after_classification["IntheJunction"] = junction_list

    # when ego on junction
    the_result_after_classification["EgoInjunction_Lane"] = fourth_list
    the_result_after_classification["EgoInjunction_junction"] = fivth_list

    return the_result_after_classification
    # print(oblist_lane_position)
