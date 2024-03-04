from .opendrive.map import Map
from .draw import draw_line, show, point
import matplotlib.path as mplPath
import numpy as np
import math
import random
import queue
def getLinearEquation(p1x, p1y, p2x, p2y):
    sign = 1
    a = p2y - p1y
    if a < 0:
        sign = -1
        a = sign * a
    b = sign * (p1x - p2x)
    c = sign * (p1y * p2x - p1x * p2y)
    return [a, b, c]

def get_signal(x):
    if int(x) < 0:
        return 0
    else:
        return 1

def allocation_amount(num_people, amount):
    # 生成小数随机数
    a = [np.random.uniform(0, amount) for i in range(num_people-1)]
    a.append(0)
    a.append(amount)
    a.sort()
    b = [a[i+1]-a[i] for i in range(num_people)]  # 列表推导式，计算列表中每两个数之间的间隔
    b = np.array(b)
    return b

class Convertor:
    def __init__(self) -> None:
        pass

    def convert(self):
        pass

class Opendrive2Apollo(Convertor):
    def __init__(self, input_file_name) -> None:
        self.xodr_map = Map()
        self.xodr_map.load(input_file_name)
        self.convert_roads()
        self.side_walk = set()
        self.road_id = set()
        self.init_side_walk_and_road_id()

    def convert_roads(self):
        for _, xodr_road in self.xodr_map.roads.items():
          xodr_road.generate_reference_line()
          xodr_road.add_offset_to_reference_line()
          # Todo(zero):
          #draw_line(xodr_road.reference_line, 'r', \
          #  reference_line = True, label = "reference line " + str(pb_road.id.id))

          xodr_road.process_lanes()
          
          #pb_last_right_section = self.convert_lane(xodr_road, pb_road)
          # Todo(zero): need to complete signal
          # self.convert_signal(xodr_road, pb_last_right_section)

    def Point_to_numpy(self, leftline, rightline):
        tmp = []
        for point in leftline:
            tmp.append([point.x, point.y])
        for point in rightline[::-1]:
            tmp.append([point.x, point.y])
        return np.array(tmp)

    def get_rotation(self, point, lane, lane2):
        x0, y0 = point
        x_point = [point.x for point in lane]
        y_point = [point.y for point in lane]
        s_point = [point.s for point in lane]
        x2_point = [point.x for point in lane2]
        y2_point = [point.y for point in lane2]
        z1_point = [point.z for point in lane]
        z2_point = [point.z for point in lane2]
        for i in range(len(x_point)):
            if i == len(x_point) - 1:
                var1 = getLinearEquation((x2_point[i] + x_point[i]) / 2, (y2_point[i] + y_point[i]) / 2, (x2_point[i-1] + x_point[i-1]) / 2, (y2_point[i-1] + y_point[i-1]) / 2)
                tmp_x = (var1[1]*var1[1] * x0 - var1[0]*var1[2] - var1[0]*var1[1]*y0) / (var1[1]*var1[1] + var1[0]*var1[0])
                tmp_y = -(var1[0] / var1[1]) * tmp_x - (var1[2] / var1[1])
                tmp_z = (z1_point[i] + z2_point[i]) / 2       
                #mid_pos = ((x2_point[i] + x_point[i]) / 2, (y2_point[i] + y_point[i]) / 2)
                mid_pos = (tmp_x, tmp_y, tmp_z)
                s = s_point[i]
                if ((x_point[i] - x_point[i - 1]) > 0) and ((y_point[i] - y_point[i - 1]) > 0):
                    return (s,mid_pos , math.atan(abs(x_point[i] - x_point[i - 1]) / abs(y_point[i] - y_point[i - 1])) * 180 / math.pi)
                elif((x_point[i] - x_point[i - 1]) > 0) and ((y_point[i] - y_point[i - 1]) < 0):
                    return (s,mid_pos ,90 + math.atan(abs(y_point[i] - y_point[i - 1]) / abs(x_point[i] - x_point[i - 1])) * 180 / math.pi)
                elif((x_point[i] - x_point[i - 1]) < 0) and ((y_point[i] - y_point[i - 1]) < 0):
                    return (s,mid_pos ,180 + math.atan(abs(x_point[i] - x_point[i - 1]) / abs(y_point[i] - y_point[i - 1])) * 180 / math.pi)
                elif((x_point[i] - x_point[i - 1]) < 0) and ((y_point[i] - y_point[i - 1]) > 0):
                    return (s,mid_pos ,270 + math.atan(abs(y_point[i] - y_point[i - 1]) / abs(x_point[i] - x_point[i - 1])) * 180 / math.pi)
            else:
                j = i + 1
            if ((x0 < x_point[i]) != (x0 < x_point[j])) or ((y0 < y_point[i]) != (y0 < y_point[j])):
                #ax + by + c = 0
                var1 = getLinearEquation((x2_point[i] + x_point[i]) / 2, (y2_point[i] + y_point[i]) / 2, (x2_point[j] + x_point[j]) / 2, (y2_point[j] + y_point[j]) / 2)
                tmp_x = (var1[1]*var1[1] * x0 - var1[0]*var1[2] - var1[0]*var1[1]*y0) / (var1[1]*var1[1] + var1[0]*var1[0])
                tmp_y = -(var1[0] / var1[1]) * tmp_x - (var1[2] / var1[1])             
                #mid_pos = ((x2_point[i] + x_point[i]) / 2, (y2_point[i] + y_point[i]) / 2)
                tmp_z = (z1_point[i] + z2_point[i]) / 2  
                mid_pos = (tmp_x, tmp_y, tmp_z)
                s = s_point[j]
                if ((x_point[j] - x_point[i]) > 0) and ((y_point[j] - y_point[i])) > 0:
                    return (s,mid_pos, math.atan(abs(x_point[j] - x_point[i]) / abs(y_point[j] - y_point[i])) * 180 / math.pi)
                elif((x_point[j] - x_point[i]) > 0) and ((y_point[j] - y_point[i])) < 0:
                    return (s,mid_pos, 90 + math.atan(abs(y_point[j] - y_point[i]) / abs(x_point[j] - x_point[i])) * 180 / math.pi)
                elif((x_point[j] - x_point[i]) < 0) and ((y_point[j] - y_point[i])) < 0:
                    return (s,mid_pos, 180 + math.atan(abs(x_point[j] - x_point[i]) / abs(y_point[j] - y_point[i])) * 180 / math.pi)
                elif((x_point[j] - x_point[i]) < 0) and ((y_point[j] - y_point[i])) > 0:
                    return (s,mid_pos, 270 + math.atan(abs(y_point[j] - y_point[i]) / abs(x_point[j] - x_point[i])) * 180 / math.pi)
        return (None, None, None)

    def is_in_road(self, point, typein, road_id):
        road = self.xodr_map.roads[str(road_id)]
        for lane_section in road.lanes.lane_sections:
            for lane in lane_section.left:
                if lane.lane_type == typein:
                    poly_path = mplPath.Path(self.Point_to_numpy(lane.left_boundary, lane.right_boundary))
                    if poly_path.contains_point(point):
                        return (True, road_id, lane.lane_id, lane)
            for lane in lane_section.right:
                if lane.lane_type == typein:
                    poly_path = mplPath.Path(self.Point_to_numpy(lane.left_boundary, lane.right_boundary))
                    if poly_path.contains_point(point):
                        return (True, road_id, lane.lane_id, lane)
        return (False, None, None, None)
    
    def get_road_and_lane_id(self, point, typein = "driving"):
        for road_id, road in self.xodr_map.roads.items():
            for lane_section in road.lanes.lane_sections:
                for lane in lane_section.left:
                    if lane.lane_type == typein:
                        poly_path = mplPath.Path(self.Point_to_numpy(lane.left_boundary, lane.right_boundary))
                        if poly_path.contains_point(point):
                            return (True, road_id, lane.lane_id)
                for lane in lane_section.right:
                    if lane.lane_type == typein:
                        poly_path = mplPath.Path(self.Point_to_numpy(lane.left_boundary, lane.right_boundary))
                        if poly_path.contains_point(point):
                            return (True, road_id, lane.lane_id)
        return (False, None, None)

    
    def get_road_point_for_create_scenario(self, point, typein = ["driving"]):
        for road_id, road in self.xodr_map.roads.items():
            for lane_section in road.lanes.lane_sections:
                for lane in lane_section.left:
                    if lane.lane_type in typein:
                        poly_path = mplPath.Path(self.Point_to_numpy(lane.left_boundary, lane.right_boundary))
                        if poly_path.contains_point(point):
                            s,mid_point, rotation = self.get_rotation(point,lane.left_boundary, lane.right_boundary)
                            return(s, rotation, mid_point, road_id, lane.lane_id)
                for lane in lane_section.right:
                    if lane.lane_type in typein:
                        poly_path = mplPath.Path(self.Point_to_numpy(lane.left_boundary, lane.right_boundary))
                        if poly_path.contains_point(point):
                            s,mid_point, rotation = self.get_rotation(point,lane.left_boundary, lane.right_boundary)
                            return(s, rotation, mid_point, road_id, lane.lane_id)
        
        return (None, None, None, None, None)
    
    def get_ran_road_point(self, road_in, typein):
        for road_id, road in self.xodr_map.roads.items():
            if int(road_id) == road_in:
                x1 = []
                y1 = []
                for lane_section in road.lanes.lane_sections:
                    for lane in lane_section.left:
                        if lane.lane_type == typein:
                            for tmp_point in lane.left_boundary:
                                x1.append(tmp_point.x)
                                y1.append(tmp_point.y)
                            for tmp_point in lane.right_boundary:
                                x1.append(tmp_point.x)
                                y1.append(tmp_point.y)
                        else:
                            continue
 
                    for lane in lane_section.right:
                        if lane.lane_type == typein:
                            for tmp_point in lane.left_boundary:
                                x1.append(tmp_point.x)
                                y1.append(tmp_point.y)
                            for tmp_point in lane.right_boundary:
                                x1.append(tmp_point.x)
                                y1.append(tmp_point.y)
                        else:
                            continue
                if len(x1) == 0 or len(y1) == 0:
                    return (None, None, None, None, None)
                x_max = max(x1)
                x_min = min(x1)
                y_max = max(y1)
                y_min = min(y1)
                count = 0
                while True:
                    count += 1
                    if count > 200:
                        break
                    ran_point = (random.uniform(x_min,x_max), random.uniform(y_min,y_max))
                    is_in, road_id, lane_id, lane = self.is_in_road(ran_point, typein, road_in)
                    if is_in:
                        if int(lane_id) == 0:
                            continue
                        s,mid_point, rotation = self.get_rotation(ran_point,lane.left_boundary, lane.right_boundary)
                        if s == None:
                            continue
                        #if abs(lane.left_boundary[-1].s - s) < 10:
                        #    continue
                        return(s,rotation, mid_point, road_id, lane_id)
        return (None, None, None, None, None)

    def get_the_roads_path(self, beg_id, beg_lane, tar_id, tar_lane):

        if int(beg_lane)  == 0:
            return None
        myqueue = queue.Queue(maxsize=0)
        myqueue.put((beg_id,beg_lane))
        pre = np.zeros((len(self.xodr_map.roads.keys())), dtype = int)
        #the_pre = np.zeros((len(self.xodr_map.roads.keys()),2), dtype = (int,int))
        the_pre = [[(0,0),(0,0)] for _ in range(len(self.xodr_map.roads.keys()))]
        pre_walk = np.zeros((len(self.xodr_map.roads.keys()),2), dtype = bool)
        is_get = False
        while not is_get:
            if(myqueue.empty()):
                #print("can't find a path from id: {} lane: {} to id: {} lane:{}!!".format(beg_id, beg_lane,tar_id,tar_lane))
                return None
        
            curry_road_id, current_lane_id = myqueue.get()
            if curry_road_id == None or tar_id == None or current_lane_id == None or tar_lane == None:
                return None
            if int(curry_road_id) == int(tar_id) and int(current_lane_id) * int(tar_lane) >  0:
                is_get = True
                break

            pre_walk[int(curry_road_id)][get_signal(current_lane_id)] = True
            current_road = self.xodr_map.roads[str(curry_road_id)]
            is_lane_get = False
            for lane_section in current_road.lanes.lane_sections:
                for current_lane in lane_section.right:
                    if int(current_lane.lane_id) == int(current_lane_id):
                        is_lane_get = True
                        break
                if is_lane_get:
                    break
                for current_lane in lane_section.left:
                    if int(current_lane.lane_id) == int(current_lane_id):
                        is_lane_get = True
                        break
                if is_lane_get:
                    break
                current_lane = None
            if current_lane == None:
                #print("the wrong road:{} with lane:{} !".format(curry_road_id, current_lane_id))
                return None

            Next = []
            next_id1 = current_road.link.successor.element_id
            type0 = current_road.link.successor.element_type
                
            next_id2 = current_road.link.predecessor.element_id
            type2 = current_road.link.predecessor.element_type

            pre_road_id = []
            if int(current_road.junction_id) != -1:
                junction = self.xodr_map.junctions[str(current_road.junction_id)]
                for con in junction.connections:
                    if int(con.connecting_road) == int(curry_road_id) and int(con.lane_links[0].to_id) * int(current_lane_id) > 0:
                        pre_road_id.append(int(con.incoming_road))
            
            Next = []
            if next_id1 != None:
                if type0  != "road" :
                    Next.append(next_id1)
                elif int(next_id1) not in pre_road_id:
                    next_lane_1 = current_lane.link.successor
                    if next_lane_1 == None:
                        next_road = self.xodr_map.roads[str(next_id1)]
                        is_lane_id_get = False
                        for lane_section in next_road.lanes.lane_sections:
                            for tmp_lane in lane_section.right:
                                predecessor = tmp_lane.link.predecessor
                                if predecessor is not None:
                                    if int(predecessor.link_id) * int(current_lane_id) > 0:
                                        if tmp_lane.center_line[0][1] < 1:
                                            continue
                                        is_lane_id_get = True
                                        next_lane_id_1 = tmp_lane.lane_id
                            if is_lane_id_get:
                                break
                            for tmp_lane in lane_section.left:
                                predecessor = tmp_lane.link.predecessor
                                if predecessor is not None:
                                    if int(predecessor.link_id) * int(current_lane_id) > 0:
                                        if tmp_lane.center_line[0][1] < 1:
                                            continue
                                        is_lane_id_get = True
                                        next_lane_id_1 = tmp_lane.lane_id
                            if is_lane_id_get:
                                break
                    else:
                        next_lane_id_1 = next_lane_1.link_id

                    next_road = self.xodr_map.roads[str(next_id1)]
                    is_lane_get = False
                    for lane_section in next_road.lanes.lane_sections:
                        for next_lane in lane_section.right:
                            if int(next_lane.lane_id) == int(next_lane_id_1):
                                is_lane_get = True
                                break
                        if is_lane_get:
                            break
                        for next_lane in lane_section.left:
                            if int(next_lane.lane_id) == int(next_lane_id_1):
                                is_lane_get = True
                                break
                        if is_lane_get:
                            break
                        next_lane = None
                    is_wrong_dir = False
                    if math.sqrt((next_lane.left_boundary[0].x-current_lane.left_boundary[-1].x)**2 + \
                        (next_lane.left_boundary[0].y-current_lane.left_boundary[-1].y)**2) > 5:
                        is_wrong_dir = True
                    if not is_wrong_dir and not pre_walk[int(next_id1)][int(get_signal(next_lane_id_1))]:
                        pre[int(next_id1)] = int(curry_road_id)
                        the_pre[int(next_id1)][get_signal(int(next_lane_id_1))] = (int(curry_road_id), int(current_lane_id))
                        myqueue.put((next_id1, next_lane_id_1))

            if next_id2 != None:
                if type2  != "road" :
                    Next.append(next_id2)
                elif int(next_id2) not in pre_road_id:
                    next_lane_2 = current_lane.link.predecessor
                    if next_lane_2 == None:
                        next_road = self.xodr_map.roads[str(next_id2)]
                        is_lane_id_get = False
                        for lane_section in next_road.lanes.lane_sections:
                            for tmp_lane in lane_section.right:
                                successor = tmp_lane.link.successor
                                if successor is not None:
                                    if int(successor.link_id) * int(current_lane_id) > 0:
                                        if tmp_lane.center_line[0][1] < 1:
                                            continue
                                        is_lane_id_get = True
                                        next_lane_id_2 = tmp_lane.lane_id
                            if is_lane_id_get:
                                break
                            for tmp_lane in lane_section.left:
                                successor = tmp_lane.link.successor
                                if successor is not None:
                                    if int(successor.link_id) * int(current_lane_id) > 0:
                                        if tmp_lane.center_line[0][1] < 1:
                                            continue
                                        is_lane_id_get = True
                                        next_lane_id_2 = tmp_lane.lane_id
                            if is_lane_id_get:
                                break
                    else:
                        next_lane_id_2 = next_lane_2.link_id
                    next_road = self.xodr_map.roads[str(next_id2)]
                    is_lane_get = False
                    for lane_section in next_road.lanes.lane_sections:
                        for next_lane in lane_section.right:
                            if int(next_lane.lane_id) == int(next_lane_id_2):
                                is_lane_get = True
                                break
                        if is_lane_get:
                            break
                        for next_lane in lane_section.left:
                            if int(next_lane.lane_id) == int(next_lane_id_2):
                                is_lane_get = True
                                break
                        if is_lane_get:
                            break
                        next_lane = None
                    is_wrong_dir = False
                    if math.sqrt((next_lane.left_boundary[0].x-current_lane.left_boundary[-1].x)**2 + \
                        (next_lane.left_boundary[0].y-current_lane.left_boundary[-1].y)**2) > 5:
                        is_wrong_dir = True
                    if not is_wrong_dir and not pre_walk[int(next_id2)][int(get_signal(next_lane_id_2))]:
                        pre[int(next_id2)] = int(curry_road_id)
                        the_pre[int(next_id2)][get_signal(int(next_lane_id_2))] = (int(curry_road_id), int(current_lane_id))
                        myqueue.put((next_id2, next_lane_id_2))

            for next_id in Next:
                junction = self.xodr_map.junctions[str(next_id)]
                for con in junction.connections:
                    if int(con.incoming_road) == int(curry_road_id) and (int(current_lane_id) * int(con.lane_links[0].from_id) > 0):
                        pre[int(con.connecting_road)] = -int(curry_road_id)
                        the_pre[int(con.connecting_road)][get_signal(int(con.lane_links[0].to_id))] = (-int(curry_road_id), int(current_lane_id))
                        if int(con.connecting_road) == int(tar_id):
                            if int(con.lane_links[0].to_id) * int(tar_lane) > 0:
                                is_get = True
                                break
                        if not pre_walk[int(con.connecting_road)][int(get_signal(con.lane_links[0].to_id))]:
                            myqueue.put((con.connecting_road ,con.lane_links[0].to_id))
            
        '''
        path = []
        path.append(int(tar_id))
        pre_id = pre[int(tar_id)]
        path.append(pre_id)
        while True:
            pre_id = pre[abs(int(pre_id))]
            if pre_id == 0:
                break
            else:
                path.append(pre_id)
                if pre_id == beg_id:
                    break
        if int(beg_id) == 0:
           path.append(beg_id)
        path = path[::-1]
        '''
        path2 = []
        path2.append((int(tar_id),int(tar_lane)))
        pre_id = the_pre[abs(int(tar_id))][get_signal(int(tar_lane))]
        path2.append(pre_id)
        while True:
            pre_id = the_pre[abs(int(pre_id[0]))][get_signal(int(pre_id[1]))]
            if int(pre_id[0]) == 0:
                break
            else:
                path2.append(pre_id)
                if int(pre_id[0]) == int(beg_id):
                    break
        if int(beg_id) == 0:
           path2.append((int(beg_id),int(beg_lane)))
        path2 = path2[::-1]
        return path2

    def get_the_lanes_path2(self, path):
        x = -1
        for point in path:
            x += 1
            next_is_junction = False
            if point[0] == 0 and x + 1 < len(path):
                next_road_id = abs(path[x + 1][0])
                next_is_junction = True
                current_road_id = abs(point[0])
                current_road = self.xodr_map.roads[str(current_road_id)]
                next1 = current_road.link.successor.element_id
                next2 = current_road.link.predecessor.element_id
                if next1 is not None and int(next1) == int(next_road_id):
                    next_is_junction = False
                if next2 is not None and int(next2) == int(next_road_id):
                    next_is_junction = False
                if int(next_road_id) == 0:
                    next_is_junction = False
            if next_is_junction or point[0] < 0:
                if x + 1 == len(path):
                    return None
                next_one = path[x+1]
                junction_road_id = next_one[0]
                current_road_id = abs(point[0])
                current_lane_id = point[1]
                junction_road = self.xodr_map.roads[str(junction_road_id)]
                junction_id = junction_road.junction_id
                junction = self.xodr_map.junctions[str(junction_id)]
                path[x] = (abs(point[0]), point[1])
                for con in junction.connections:
                    from_lane_id = 0
                    if int(con.incoming_road) == int(current_road_id) and (int(con.connecting_road) == int(junction_road_id)):
                        from_lane_id = con.lane_links[0].from_id
                    if from_lane_id != 0 and int(current_lane_id) != int(from_lane_id):
                        differ = int(from_lane_id) - int(current_lane_id)
                        differ = differ / abs(differ)
                        next_lane_1 = int(current_lane_id) + differ
                        count = 1
                        while True:
                            path.insert(x+count,(abs(current_road_id),int(next_lane_1)))
                            if next_lane_1 == int(from_lane_id):
                                break
                            next_lane_1 += differ
                            count += 1
                
            elif x + 1 < len(path):
                next_one = path[x+1]
                next_road_id = abs(next_one[0])
                if abs(int(next_one[0])) == abs(int(point[0])):
                    continue
                current_road_id = abs(point[0])
                current_lane_id = point[1]
                current_road = self.xodr_map.roads[str(current_road_id)]
                is_break = False
                for lane_section in current_road.lanes.lane_sections:
                    for lane in lane_section.left:
                        if int(lane.lane_id) == int(current_lane_id):
                            current_lane = lane
                            is_break = True
                            break
                    for lane in lane_section.right:
                        if int(lane.lane_id) == int(current_lane_id):
                            current_lane = lane
                            is_break = True
                            break
                    if is_break:
                        break
                if int(current_road.link.successor.element_id) == int(next_road_id):
                    if current_lane.link.successor is not None:
                        next_lane = current_lane.link.successor.link_id
                    else:
                        continue
                else:
                    if current_lane.link.predecessor is not None:
                        next_lane = current_lane.link.predecessor.link_id
                    else:
                        continue
                if int(next_lane) != int(next_one[1]):
                    differ = int(next_one[1]) - int(next_lane)
                    differ = differ / abs(differ)
                    next_lane_1 = int(next_lane)
                    count = 1
                    while next_lane_1 != int(next_one[1]):
                        path.insert(x+count,(abs(next_road_id),int(next_lane_1)))
                        next_lane_1 += differ
                        count += 1
        return path

    def get_simple_rotation(self, tmp_x,tmp_y,past_x,past_y):
        if ((tmp_x - past_x) > 0) and ((tmp_y - past_y)) > 0:
            rotation =  (math.atan(abs(tmp_x - past_x) / abs(tmp_y - past_y)) * 180 / math.pi)
        elif((tmp_x - past_x) > 0) and ((tmp_y - past_y)) < 0:
            rotation =  90 + (math.atan( abs(tmp_y - past_y) / abs(tmp_x - past_x)) * 180 / math.pi)
        elif((tmp_x - past_x) < 0) and ((tmp_y - past_y)) < 0:
            rotation =  180 + (math.atan(abs(tmp_x - past_x) / abs(tmp_y - past_y)) * 180 / math.pi)
        elif((tmp_x - past_x) < 0) and ((tmp_y - past_y)) > 0:
            rotation =  270 + (math.atan(abs(tmp_y - past_y) / abs(tmp_x - past_x)) * 180 / math.pi)
        return rotation

    def get_waypoint(self, lane_path, begin_point, first_s, end_point, last_s):
        count = 0
        result = []
        result.append(begin_point)
        is_begin = True
        is_end = False
        while not is_end:
            point_s = []
            current_road_id, current_lane_id = lane_path[count]
            current_road = self.xodr_map.roads[str(current_road_id)]
            if int(current_road.junction_id) != -1:
                sample_rate = 5
            else:
                sample_rate = 3
            # 在一条road中，变了几次道，从而拆分从哪开始变道
            tmp_count = 1
            begin_s = 0
            for lane_section in current_road.lanes.lane_sections:
                for lane in lane_section.left:
                    if int(lane.lane_id) == int(current_lane_id):
                        current_lane = lane
                        is_break = True
                        break
                for lane in lane_section.right:
                    if int(lane.lane_id) == int(current_lane_id):
                        current_lane = lane
                        is_break = True
                        break
                if is_break:
                    break
            if current_lane == None:
                print("!!!!!!")
            end_s = len(current_lane.center_line)

            while count + tmp_count < len(lane_path):   
                next_road_id, _ = lane_path[count + tmp_count]
                if int(next_road_id) != int(current_road_id):
                    break 
                else: # lane change
                    tmp_count += 1
            if count +tmp_count >= len(lane_path):
                is_end = True

            if is_begin: #  初始位置，有s的限制
                is_begin = False
                begin_s = first_s
            # 因为这个s是road的s，而后续用的是lane的center_line进行判断（即center_line[0]是代表该方向的起始点，但其s可能不为0）
            # 所以需要进行转换，将s 与center_line的下标进行对应
                # 拿到当前的lane对象
                if current_lane.center_line[0][0].s != 0:
                    for x in range(len(current_lane.center_line) - 1):
                        if current_lane.center_line[x][0].s >= first_s >= current_lane.center_line[x+1][0].s <= first_s:
                            begin_s = x
                            break
                
            if is_end:
                end_s = last_s
                #同理
                if current_lane.center_line[0][0].s != 0:
                    for x in range(len(current_lane.center_line) - 1):
                        if current_lane.center_line[x][0].s >= last_s and current_lane.center_line[x+1][0].s <= last_s:
                            end_s = x
                            break

            s_lenth = end_s - begin_s
            local_get = allocation_amount(tmp_count,1)
            point_s.append((begin_s, begin_s + local_get[0] * s_lenth))
            for x in local_get[1:]:
                last_one_s = point_s[-1][1]
                point_s.append((min(last_one_s + 0.05 * s_lenth, last_one_s + x * s_lenth), last_one_s + x * s_lenth))
            is_break = False
            for local in range(0,tmp_count):
                #每一个lane 的s获取
                current_lane = None
                _, current_lane_id = lane_path[count + local]
                for lane_section in current_road.lanes.lane_sections:
                    for lane in lane_section.left:
                        if int(lane.lane_id) == int(current_lane_id):
                            current_lane = lane
                            is_break = True
                            break
                    for lane in lane_section.right:
                        if int(lane.lane_id) == int(current_lane_id):
                            current_lane = lane
                            is_break = True
                            break
                    if is_break:
                        break
                if current_lane == None:
                    print("!!!!!!!!")
                    return None
                begin_s_one = point_s[local][0]
                end_s_one = point_s[local][1]
                choice = range(math.ceil(begin_s_one),math.floor(end_s_one))
                #在一条lane里面，随机选取相应的点，然后进行排序，进行坐标获取
                ran_point = random.sample(choice,min(int((end_s_one - begin_s_one)  / sample_rate), len(choice)))
                ran_point.sort()
                the_first_lane_waypoint = True
                if current_lane.center_line[0][0].s > 0.5:
                    direction = -1
                else:
                    direction = 0
                for waypoint in ran_point:
                    tmp_width = current_lane.center_line[waypoint][1]
                    if tmp_width < 1:
                        continue
                    tmp_x = current_lane.center_line[waypoint][0].x
                    tmp_y = current_lane.center_line[waypoint][0].y
                    tmp_z = current_lane.center_line[waypoint][0].z
                    '''
                    if direction == -1:
                        rota = current_lane.center_line[waypoint][0].yaw
                        tmp_rotation = -(rota / abs(rota))*(math.pi - abs(rota)) * 180 / math.pi
                    else:
                        tmp_rotation = current_lane.center_line[waypoint][0].yaw * 180 / math.pi
                    tmp_rotation = (360 + (90 - tmp_rotation)) % 360
                    past_x, past_y, _, last_rotation = result[-1]
                    rotation = self.get_simple_rotation(tmp_x,tmp_y,past_x,past_y)
                    if the_first_lane_waypoint:
                        the_first_lane_waypoint = False
                        if abs(last_rotation - rotation) > 45:
                            return None
                        else:
                            result.append((tmp_x, tmp_y, tmp_z, rotation))
                    if abs(last_rotation - rotation) < 90:
                        result.append((tmp_x, tmp_y, tmp_z, tmp_rotation))
                    '''
                    past_x, past_y, _, last_rotation = result[-1]
                    rotation = self.get_simple_rotation(tmp_x,tmp_y,past_x,past_y)
                    big_one = max(last_rotation, rotation)
                    small_one = min(last_rotation, rotation)
                    if the_first_lane_waypoint:
                        the_first_lane_waypoint = False
                        if(360 - big_one + small_one) > 30 and (big_one - small_one) > 30:
                            return None
                    elif (360 - big_one + small_one) > 30 and (big_one - small_one) > 30:
                        continue
                    else:
                        result.append((tmp_x, tmp_y, tmp_z, rotation))
                if len(result) > 2:
                    last_one_rotation = result[-1][3]
                    last_two_rotaiton = result[-2][3]
                    big_one = max(last_one_rotation, last_two_rotaiton)
                    small_one = min(last_one_rotation, last_two_rotaiton)
                    if(360 - big_one + small_one) > 30 and (big_one - small_one) > 30:
                        return None
            count += tmp_count
        past_x, past_y, _, last_rotation = result[-1]
        rotation = self.get_simple_rotation(end_point[0],end_point[1],past_x,past_y)
        big_one = max(last_rotation, rotation)
        small_one = min(last_rotation, rotation)
        if (360 - big_one + small_one) > 30 and (big_one - small_one) > 30:
            return None   
        big_one = max(end_point[3], rotation)
        small_one = min(end_point[3], rotation)
        if (360 - big_one + small_one) > 30 and (big_one - small_one) > 30:
            return None   
        result.append((end_point[0],end_point[1],end_point[2],rotation))
        result.append(end_point)
        return result

    def init_side_walk_and_road_id(self):
        for road_id, road in self.xodr_map.roads.items():
            for lane_section in road.lanes.lane_sections:
                for lane in lane_section.left:
                    if lane.lane_type == "sidewalk":
                        self.side_walk.add(road_id)
                        break
                    elif lane.lane_type == "driving":
                        self.road_id.add(road_id)
                        break
                    else:
                        continue
 
                for lane in lane_section.right:
                    if lane.lane_type == "sidewalk":
                        self.side_walk.add(road_id)
                        break
                    elif lane.lane_type == "driving":
                        self.road_id.add(road_id)
                        break
                    else:
                        continue

    def cross_road_waypoint(self, road_id):
        road = self.xodr_map.roads[str(road_id)]

        for lane_section in road.lanes.lane_sections:
            left_most = lane_section.leftmost_boundary()
            right_most = lane_section.rightmost_boundary()
        which_side = random.randint(0,1)
        if which_side == 0:
            begin_side = left_most[0]
            end_side = right_most[0]
        else:
            begin_side = right_most[0]
            end_side = left_most[0]
        the_place = random.randint(0, len(right_most[0]) - 1)
        begin_palce = begin_side[the_place]
        end_palce = end_side[the_place]
        rotation = self.get_simple_rotation(begin_palce.x, begin_palce.y, end_palce.x, end_palce.y)
        begin_position = (begin_palce.x, begin_palce.y, begin_palce.z, rotation)
        end_position = (end_palce.x, end_palce.y, end_palce.z, rotation)
        #point((begin_palce.x, begin_palce.y, begin_palce.z))
        #point((end_palce.x, end_palce.y, end_palce.z))
        return left_most[0],right_most[0], begin_position, end_position


    '''
    def get_the_Lanes_path(self, beg_lane, tar_lane, road_paths):
        count = 0
        result_lane_path = []
        result_lane_path.append((abs(road_paths[0]),str(beg_lane)))
        for current_road_id in road_paths:
            count += 1
            next_is_junction = False
            if current_road_id == 0 and count < len(road_paths):
                next_road_id = road_paths[count]
                next_is_junction = True
                current_road = self.xodr_map.roads[str(current_road_id)]
                next1 = current_road.link.successor.element_id
                next2 = current_road.link.predecessor.element_id
                if next1 is not None and int(next1) == int(next_road_id):
                    next_is_junction = False
                if next2 is not None and int(next2) == int(next_road_id):
                    next_is_junction = False

            if next_is_junction or current_road_id < 0:
                if count >= len(road_paths):
                    return []
                else:
                    current_road_id = abs(current_road_id)
                    junction_road_id = road_paths[count]
                    junction_road = self.xodr_map.roads[str(junction_road_id)]
                    junction_id = junction_road.junction_id
                    junction = self.xodr_map.junctions[str(junction_id)]
                    for con in junction.connections:
                        if int(con.incoming_road) == int(current_road_id) and (int(con.connecting_road) == int(junction_road_id)):
                            from_lane_id = con.lane_links[0].from_id
                            to_lane_id = con.lane_links[0].to_id
                    _, current_lane_id = result_lane_path[-1]
                    if int(current_lane_id) != int(from_lane_id):
                        result_lane_path.append((abs(current_road_id),from_lane_id))
                    result_lane_path.append((abs(junction_road_id), to_lane_id))

            else:
                if count >= len(road_paths):
                    break
                else:
                    is_break = False
                    _, current_lane_id = result_lane_path[-1]
                    current_road = self.xodr_map.roads[str(current_road_id)]
                    for lane_section in current_road.lanes.lane_sections:
                        for lane in lane_section.left:
                            if int(lane.lane_id) == int(current_lane_id):
                                current_lane = lane
                                is_break = True
                                break
                        for lane in lane_section.right:
                            if int(lane.lane_id) == int(current_lane_id):
                                current_lane = lane
                                is_break = True
                                break
                        if is_break:
                            break
                    if count < 2:
                        next_road_id = road_paths[count]
                        if int(current_road.link.successor.element_id) == int(next_road_id):
                            if current_lane.link.successor is not None:
                                next_lane = current_lane.link.successor.link_id
                            else:
                                next_lane = current_lane.link.predecessor.link_id
                        else:
                            if current_lane.link.predecessor is not None:
                                next_lane = current_lane.link.predecessor.link_id
                            else:
                                next_lane = current_lane.link.successor.link_id
                    else:
                        _, past_lane_id = result_lane_path[-2]
                        if current_lane.link.successor is not None and current_lane.link.successor.link_id != past_lane_id:
                            next_lane = current_lane.link.successor.link_id
                        elif current_lane.link.predecessor is not None and current_lane.link.predecessor.link_id != past_lane_id:
                            next_lane = current_lane.link.predecessor.link_id
                        else:
                            next_lane = past_lane_id
                    result_lane_path.append((abs(road_paths[count]),next_lane))
        
        end_road, current_lane = result_lane_path[-1]
        if int(current_lane) != int(tar_lane):
            result_lane_path.append((abs(end_road),str(tar_lane)))
        return result_lane_path
    '''
                    
                