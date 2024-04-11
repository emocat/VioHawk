import json
import warnings

import numpy as np

from shapely.geometry import LineString, Point
from shapely.geometry import Polygon

directory = '../map/'

_type_of_signals = {"1":"UNKNOWN", \
                    "2":"CIRCLE", \
                    "3":"ARROW_LEFT", \
                    "4":"ARROW_FORWARD", \
                    "5":"ARROW_RIGHT", \
                    "6":"ARROW_LEFT_AND_FORWARD", \
                    "7":"ARROW_RIGHT_AND_FORWARD", \
                    "8":"ARROW_U_TURN", \
                     }
  # enum Type {
  #   UNKNOWN = 1;
  #   CIRCLE = 2;
  #   ARROW_LEFT = 3;
  #   ARROW_FORWARD = 4;
  #   ARROW_RIGHT = 5;
  #   ARROW_LEFT_AND_FORWARD = 6;
  #   ARROW_RIGHT_AND_FORWARD = 7;
  #   ARROW_U_TURN = 8;
  # };


  # enum LaneTurn {
  #   NO_TURN = 1;
  #   LEFT_TURN = 2;
  #   RIGHT_TURN = 3;
  #   U_TURN = 4;
  # };

class get_map_info:
    def __init__(self, map_name):
        self.file = directory + map_name + ".json"
        self.lane_config = dict()
        self.lane_waypoints = dict()
        self.lane_turn =dict()

        self.areas = dict()

        self.crosswalk_config = dict()
        self.traffic_sign = []
        self.traffic_signals = []
        self.Roads = []

        self.original_map = dict()

        with open(self.file) as f:
            self.areas["lane_areas"] = dict()
            self.areas["junction_areas"] = dict()

            map_config = json.load(f)
            self.original_map = map_config
            lane = map_config['laneList']
            junction = map_config['junctionList']
            crosswalk = map_config['crosswalkList']
            trafficSign = map_config['stopSignList']
            Signals = map_config['signalList']
            Roads = map_config['roadList']

            for i in range(len(lane)):
                lane_id = lane[i]['id']['id']
                lane_length = lane[i]['length']
                self.lane_config[lane_id] = lane_length
                self.lane_waypoints[lane_id] = []
                self.lane_turn[lane_id] = lane[i]["turn"]
                for _i in range(len(lane[i]['centralCurve']['segmentList'])):
                    lane_segment_point = lane[i]['centralCurve']['segmentList'][_i]['lineSegment']['pointList']
                    for k in range(len(lane_segment_point)):
                        _wp_k = lane_segment_point[k]
                        self.lane_waypoints[lane_id].append(np.array([_wp_k['x'], _wp_k['y']]))

                area_lane_left = []
                for _ii in range(len(lane[i]['leftBoundary']['curve']['segmentList'])):
                    leftBoundary_point = lane[i]['leftBoundary']['curve']['segmentList'][_ii]['lineSegment']['pointList']
                    for k in range(len(leftBoundary_point)):
                        _wp_k0 = leftBoundary_point[k]
                        area_lane_left.append((_wp_k0['x'], _wp_k0['y']))

                area_lane_right = []
                for _iii in range(len(lane[i]['rightBoundary']['curve']['segmentList'])):
                    rightBoundary_point = lane[i]['rightBoundary']['curve']['segmentList'][_iii]['lineSegment']['pointList']
                    for k in range(len(rightBoundary_point)):
                        _wp_k1 = rightBoundary_point[k]
                        area_lane_right.append((_wp_k1['x'], _wp_k1['y']))

                area_lane_right.reverse()
                single_lane_area = []
                single_lane_area = area_lane_left + area_lane_right
                # print(single_lane_area)
                self.areas["lane_areas"][lane_id] = single_lane_area

            for _junction in junction:
                junction_id = _junction['id']['id']
                temp = []
                junction_polygon = _junction['polygon']['pointList']
                for _point in junction_polygon:
                    temp.append((_point['x'],_point['y']))
                self.areas["junction_areas"][junction_id] = temp

            for j in range(len(crosswalk)):
                crosswalk_polygon = crosswalk[j]['polygon']['pointList']
                if len(crosswalk_polygon) != 4:
                    print('Needs four points to describe a crosswalk!')
                    exit()
                crosswalk_points = [(crosswalk_polygon[0]['x'], crosswalk_polygon[0]['y']),
                                    (crosswalk_polygon[1]['x'], crosswalk_polygon[1]['y']),
                                    (crosswalk_polygon[2]['x'], crosswalk_polygon[2]['y']),
                                    (crosswalk_polygon[3]['x'], crosswalk_polygon[3]['y'])
                                    ]
                self.crosswalk_config['crosswalk'+str(j+1)] = crosswalk_points

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
                self.Roads.append(single_element)


    def get_lane_config(self):
        return self.lane_config

    def get_crosswalk_config(self):
        return self.crosswalk_config

    def get_traffic_sign(self):
        return self.traffic_sign

    def get_traffic_signals(self):
        return self.traffic_signals

    def get_position(self, lane_position): #convert lane_position to normal one
        ## lane_position = [lane_id, offset]
        lane_id = lane_position[0]
        offset = lane_position[1]
        waypoint = self.lane_waypoints[lane_id]
        _distance = 0
        for i in range(len(waypoint)-1):
            wp1 = waypoint[i]
            wp2 = waypoint[i+1]
            _dis_wp1_2 = np.linalg.norm(wp1 - wp2)
            if _distance + _dis_wp1_2 > offset:
                current_dis = offset - _distance
                k = current_dis / _dis_wp1_2
                x = wp1[0] + (wp2[0] - wp1[0])*k
                y = wp1[1] + (wp2[1] - wp1[1])*k
                return (x, y, 0)
            _distance += _dis_wp1_2
        if i == len(waypoint)-2:
            warnings.warn("The predefined position is out of the given lane, set to the end of the lane.")
            return (wp2[0], wp2[1], 0)

    def get_position2(self, position): #convert normal one to lane_position
        position2 = np.array([position['x'], position['y']])
        # print(position2)

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
                # print( waypoints[0])
                dis0 = np.linalg.norm(position2 - waypoints[0])
                nearest_point = 0
                for _i in range(len(waypoints)):
                    if np.linalg.norm(position2 - waypoints[_i]) < dis0:
                        nearest_point = _i
                        dis0 = np.linalg.norm(position2 - waypoints[_i])
                    # if _i == 0:
                    #     pass 
                    # else:
                    #     dsiatance.append(np.linalg.norm(waypoints[_i] - waypoints[_i-1]))
                offset = 0

                tt = nearest_point

                if tt > 0:
                    offset += np.linalg.norm(waypoints[tt] - waypoints[tt-1])
                    tt -= 1

                result["offset"] = offset + np.linalg.norm(position2 - waypoints[nearest_point])


        return result
        ## lane_position = [lane_id, offset]
        # lane_id = lane_position[0]
        # offset = lane_position[1]

        # waypoint = self.lane_waypoints[lane_id]
        # _distance = 0
        # for i in range(len(waypoint)-1):
        #     wp1 = waypoint[i]
        #     wp2 = waypoint[i+1]
        #     _dis_wp1_2 = np.linalg.norm(wp1 - wp2)
        #     if _distance + _dis_wp1_2 > offset:
        #         current_dis = offset - _distance
        #         k = current_dis / _dis_wp1_2
        #         x = wp1[0] + (wp2[0] - wp1[0])*k
        #         y = wp1[1] + (wp2[1] - wp1[1])*k
        #         return (x, y, 0)
        #     _distance += _dis_wp1_2

        # if i == len(waypoint)-2:
        #     warnings.warn("The predefined position is out of the given lane, set to the end of the lane.")
        #     return (wp2[0], wp2[1], 0)


    def check_whether_in_lane_area(self, point):
        result = []
        for key in self.areas["lane_areas"]:
            points = []
            points = self.areas["lane_areas"][key]
            # print(points)
            the_area = Polygon(points)   
            # print(the_area.area)   
            one = {}      
            if point.distance(the_area)==0:
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
            # print(points)
            the_area = Polygon(points)   
            # print(the_area.area)  
            one = {}        
            if point.distance(the_area)==0:
                # print('In junction: '+ str(key))
                one["junction_id"] = key
                result.append(one)
        return result

    def find_which_area_the_point_is_in(self, point):
        # print(point)
        _point = Point(point)

        result = self.check_whether_in_junction_area(_point)
        if result != []:
            # print(result)
            return result

        result = self.check_whether_in_lane_area(_point)
        if result != []:
            # print(result)
            return result           
        return None

    def find_which_area_the_ego_is_in(self, ego):
        # print(point)
        # _point = Point(point)

        result = self.check_whether_in_junction_area(ego)
        if result != []:
            # print(result)
            return result

        result = self.check_whether_in_lane_area(ego)
        if result != []:
            # print(result)
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
                if flag0==1 and flag1 ==1:
                    return True 
        return False
        



if __name__ == "__main__":
    map = "san_francisco"
    map_info = get_map_info(map)
    map_info.get_lane_config()
    # print(map_info)
    test =  map_info.get_traffic_sign()
    # print(test)

    lane_point = ["lane_38",25]
    p = map_info.get_position(lane_point)

    print(p)

    # (553068.4194627955, 4182683.858571535, 0)

    pp= {"x": 553063.4194634936,"y": 4182683.8559292993,"z": 0}

    p = map_info.get_position2(pp)

    print(p)

    # map_info.find_which_area_the_point_is_in((p[0],p[1]))
    # print(p)
