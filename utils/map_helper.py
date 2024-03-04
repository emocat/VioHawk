import json
import warnings

import numpy as np

from shapely.geometry import LineString, Point
from shapely.geometry import Polygon

_type_of_signals = {
    "1": "UNKNOWN",
    "2": "CIRCLE",
    "3": "ARROW_LEFT",
    "4": "ARROW_FORWARD",
    "5": "ARROW_RIGHT",
    "6": "ARROW_LEFT_AND_FORWARD",
    "7": "ARROW_RIGHT_AND_FORWARD",
    "8": "ARROW_U_TURN",
}


class get_map_info:
    def __init__(self, map_path):
        self.file = map_path
        self.lane_config = dict()
        self.lane_waypoints = dict()
        self.lane_turn = dict()
        self.lane_speed_limit = dict()

        self.areas = dict()

        self.crosswalk_config = dict()
        self.traffic_sign = []
        self.traffic_signals = []
        self.Roads = []

        self.original_map = dict()

        with open(self.file) as f:
            self.areas["lane_areas"] = dict()
            self.areas["junction_areas"] = dict()
            self.areas["lane_areas_left"] = dict()
            self.areas["lane_areas_right"] = dict()

            map_config = json.load(f)
            self.original_map = map_config
            lane = map_config["laneList"]
            junction = map_config["junctionList"]
            crosswalk = map_config["crosswalkList"]
            trafficSign = map_config["stopSignList"]
            Signals = map_config["signalList"]
            Roads = map_config["roadList"]

            for i in range(len(lane)):
                lane_id = lane[i]["id"]["id"]
                lane_length = lane[i]["length"]
                self.lane_config[lane_id] = lane_length
                self.lane_waypoints[lane_id] = []
                self.lane_turn[lane_id] = lane[i]["turn"]
                self.lane_speed_limit[lane_id] = lane[i]["speedLimit"]
                for _i in range(len(lane[i]["centralCurve"]["segmentList"])):
                    lane_segment_point = lane[i]["centralCurve"]["segmentList"][_i]["lineSegment"]["pointList"]
                    for k in range(len(lane_segment_point)):
                        _wp_k = lane_segment_point[k]
                        self.lane_waypoints[lane_id].append(np.array([_wp_k["x"], _wp_k["z"]]))

                area_lane_left = []
                for _ii in range(len(lane[i]["leftBoundary"]["curve"]["segmentList"])):
                    leftBoundary_point = lane[i]["leftBoundary"]["curve"]["segmentList"][_ii]["lineSegment"][
                        "pointList"
                    ]
                    for k in range(len(leftBoundary_point)):
                        _wp_k0 = leftBoundary_point[k]
                        area_lane_left.append((_wp_k0["x"], _wp_k0["z"]))

                area_lane_right = []
                for _iii in range(len(lane[i]["rightBoundary"]["curve"]["segmentList"])):
                    rightBoundary_point = lane[i]["rightBoundary"]["curve"]["segmentList"][_iii]["lineSegment"][
                        "pointList"
                    ]
                    for k in range(len(rightBoundary_point)):
                        _wp_k1 = rightBoundary_point[k]
                        area_lane_right.append((_wp_k1["x"], _wp_k1["z"]))

                self.areas["lane_areas_left"][lane_id] = area_lane_left
                self.areas["lane_areas_right"][lane_id] = area_lane_right

                area_lane_right.reverse()
                single_lane_area = []
                single_lane_area = area_lane_left + area_lane_right
                # print(single_lane_area)
                self.areas["lane_areas"][lane_id] = single_lane_area

            for _junction in junction:
                junction_id = _junction["id"]["id"]
                temp = []
                junction_polygon = _junction["polygon"]["pointList"]
                for _point in junction_polygon:
                    temp.append((_point["x"], _point["z"]))
                self.areas["junction_areas"][junction_id] = temp

            for j in range(len(crosswalk)):
                crosswalk_polygon = crosswalk[j]["polygon"]["pointList"]
                if len(crosswalk_polygon) != 4:
                    print("Needs four points to describe a crosswalk!")
                    exit()
                crosswalk_points = [
                    (crosswalk_polygon[0]["x"], crosswalk_polygon[0]["z"]),
                    (crosswalk_polygon[1]["x"], crosswalk_polygon[1]["z"]),
                    (crosswalk_polygon[2]["x"], crosswalk_polygon[2]["z"]),
                    (crosswalk_polygon[3]["x"], crosswalk_polygon[3]["z"]),
                ]
                self.crosswalk_config["crosswalk" + str(j + 1)] = crosswalk_points

            for _i in trafficSign:
                single_element = {}
                single_element["id"] = _i["id"]["id"]
                if single_element["id"].find("stopsign") != -1:
                    single_element["type"] = "stopsign"
                    stop_line_points = []
                    if _i.__contains__("stopLineList"):
                        stop_line_points = _i["stopLineList"][0]["segmentList"][0]["lineSegment"]["pointList"]
                    single_element["stop_line_points"] = stop_line_points

                else:
                    single_element["type"] = None
                self.traffic_sign.append(single_element)

            for _i in Signals:
                single_element = {}
                single_element["id"] = _i["id"]["id"]
                # if single_element["id"].find("stopsign") != -1:
                #     single_element["type"] = "stopsign"
                if _i.__contains__("boundary"):
                    single_element["point"] = _i["boundary"]["pointList"][0]
                sub_signal_type_list = []
                if _i.__contains__("subsignalList"):
                    for _j in _i["subsignalList"]:
                        num_type = _j["type"]
                        sub_signal_type_list.append(_type_of_signals[str(num_type)])
                single_element["sub_signal_type_list"] = sub_signal_type_list
                if _i.__contains__("stopLineList"):
                    stop_line_points = _i["stopLineList"][0]["segmentList"][0]["lineSegment"]["pointList"]
                single_element["stop_line_points"] = stop_line_points
                self.traffic_signals.append(single_element)

            for _i in Roads:
                single_element = {}
                single_element["id"] = _i["id"]["id"]
                temp = []
                _list = _i["sectionList"][0]["laneIdList"]
                for kk in _list:
                    ID = kk["id"]
                    temp.append(ID)
                single_element["laneIdList"] = temp

                single_element["roadpointList"] = []
                _list = _i["sectionList"][0]["boundary"]["outerPolygon"]["edgeList"]
                for _j in _list:
                    for _k in _j["curve"]["segmentList"][0]["lineSegment"]["pointList"]:
                        single_element["roadpointList"].append(np.array([_k["x"], _k["z"]]))

                self.Roads.append(single_element)

    def get_lane_config(self):
        return self.lane_config

    def get_crosswalk_config(self):
        return self.crosswalk_config

    def get_traffic_sign(self):
        return self.traffic_sign

    def get_traffic_signals(self):
        return self.traffic_signals

    def get_position(self, lane_position):  # convert lane_position to normal one
        lane_id = lane_position[0]
        offset = lane_position[1]
        waypoint = self.lane_waypoints[lane_id]
        _distance = 0
        for i in range(len(waypoint) - 1):
            wp1 = waypoint[i]
            wp2 = waypoint[i + 1]
            _dis_wp1_2 = np.linalg.norm(wp1 - wp2)
            if _distance + _dis_wp1_2 > offset:
                current_dis = offset - _distance
                k = current_dis / _dis_wp1_2
                x = wp1[0] + (wp2[0] - wp1[0]) * k
                y = wp1[1] + (wp2[1] - wp1[1]) * k
                return (x, y, 0)
            _distance += _dis_wp1_2
        if i == len(waypoint) - 2:
            warnings.warn("The predefined position is out of the given lane, forcely set the point.")
            more_dis = offset - _distance
            k = more_dis / _dis_wp1_2
            x = wp2[0] + (wp2[0] - wp1[0]) * k
            y = wp2[1] + (wp2[1] - wp1[1]) * k
            return (x, y, 0)

    def get_position2(self, position):  # convert normal one to lane_position
        position2 = np.array([position["x"], position["y"]])

        point = Point(position2)
        temp = 100000
        result = {}
        for key in self.areas["lane_areas"]:
            points = []
            points = self.areas["lane_areas"][key]
            the_area = Polygon(points)
            if point.distance(the_area) < temp:
                temp = point.distance(the_area)
                result["lane"] = key
                waypoints = self.lane_waypoints[key]
                dsiatance = []
                dis0 = np.linalg.norm(position2 - waypoints[0])
                nearest_point = 0
                for _i in range(len(waypoints)):
                    if np.linalg.norm(position2 - waypoints[_i]) < dis0:
                        nearest_point = _i
                        dis0 = np.linalg.norm(position2 - waypoints[_i])
                offset = 0
                tt = nearest_point

                while tt > 0:
                    offset += np.linalg.norm(waypoints[tt] - waypoints[tt - 1])
                    tt -= 1

                if nearest_point > 0:
                    x1 = np.linalg.norm(position2 - waypoints[nearest_point - 1])
                    x2 = np.linalg.norm(waypoints[nearest_point] - waypoints[nearest_point - 1])
                    if x1 < x2:
                        result["offset"] = offset - np.linalg.norm(position2 - waypoints[nearest_point])
                    else:
                        result["offset"] = offset + np.linalg.norm(position2 - waypoints[nearest_point])
                else:
                    result["offset"] = offset + np.linalg.norm(position2 - waypoints[nearest_point])

        return result

    def check_whether_in_lane_area(self, point):
        result = []
        for key in self.areas["lane_areas"]:
            points = []
            points = self.areas["lane_areas"][key]
            # print(points)
            the_area = Polygon(points)
            # print(the_area.area)
            one = {}
            if point.distance(the_area) < 0.3:
                # print('In lane: '+ str(key))
                one["lane_id"] = key
                one["turn"] = self.lane_turn[key]
                one["laneNumber"] = self.check_lane_number_of_road(key)
                result.append(one)
        return result

    def check_lane_number_of_road(self, lane):
        for _i in self.Roads:
            for _j in _i["laneIdList"]:
                number = len(_i["laneIdList"])
                if lane == _j:
                    return number
        return 0

    def check_whether_in_junction_area(self, point):
        result = []
        for key in self.areas["junction_areas"]:
            points = []
            points = self.areas["junction_areas"][key]
            the_area = Polygon(points)
            one = {}
            if point.distance(the_area) == 0:
                one["junction_id"] = key
                result.append(one)
        return result

    def find_which_area_the_point_is_in(self, point):
        _point = Point(point)

        result = self.check_whether_in_junction_area(_point)
        if result != []:
            return result

        result = self.check_whether_in_lane_area(_point)
        if result != []:
            return result
        return None

    def find_which_area_the_ego_is_in(self, ego):
        result = self.check_whether_in_junction_area(ego)
        if result != []:
            return result

        result = self.check_whether_in_lane_area(ego)
        if result != []:
            return result
        return None

    def check_whether_two_lanes_are_in_the_same_road(self, lane_1, lane_2):
        for _i in self.Roads:
            flag0 = 0
            flag1 = 0
            for _j in _i["laneIdList"]:
                if lane_1 == _j:
                    flag0 = 1
                if lane_2 == _j:
                    flag1 = 1
                if flag0 == 1 and flag1 == 1:
                    return True
        return False

    def get_reverse_lanes(self, lane):
        for road in self.Roads:
            lane_list = road["laneIdList"]
            if lane in lane_list:
                lane_idx = lane_list.index(lane)
                if lane_idx >= len(lane_list) / 2:
                    return lane_list[: len(lane_list) // 2]
                else:
                    return lane_list[len(lane_list) // 2 :]

    def get_left_lane(self, lane):
        for road in self.Roads:
            lane_list = road["laneIdList"]
            if lane in lane_list:
                lane_idx = lane_list.index(lane)
                if lane_idx >= len(lane_list) / 2:
                    if lane_idx > 0:
                        return lane_list[lane_idx - 1]
                    else:
                        return None
                else:
                    if lane_idx < len(lane_list) - 1:
                        return lane_list[lane_idx + 1]
                    else:
                        return None

    def get_right_lane(self, lane):
        for road in self.Roads:
            lane_list = road["laneIdList"]
            if lane in lane_list:
                lane_idx = lane_list.index(lane)
                if lane_idx >= len(lane_list) / 2:
                    if lane_idx < len(lane_list) - 1:
                        return lane_list[lane_idx + 1]
                    else:
                        return None
                else:
                    if lane_idx > 0:
                        return lane_list[lane_idx - 1]
                    else:
                        return None

    def get_adjacent_lanes(self, lane):
        for road in self.Roads:
            lane_list = road["laneIdList"]
            if lane in lane_list:
                lane_idx = lane_list.index(lane)
                if lane_idx - 1 >= 0:
                    left_lane = lane_list[lane_idx - 1]
                else:
                    left_lane = None
                if lane_idx + 1 < len(lane_list):
                    right_lane = lane_list[lane_idx + 1]
                else:
                    right_lane = None
                return left_lane, right_lane
