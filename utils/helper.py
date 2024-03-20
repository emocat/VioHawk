import math
import json
import lgsvl
import numpy as np

from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union


def calc_distance(pos1, pos2):
    if isinstance(pos1, dict):
        if "Position" in pos1:
            pos1_x = pos1["Position"]["x"]
            pos1_z = pos1["Position"]["z"]
        elif "z" in pos1:
            pos1_x = pos1["x"]
            pos1_z = pos1["z"]
        elif "y" in pos1:
            pos1_x = pos1["x"]
            pos1_z = pos1["y"]
        else:
            assert False, "pos1 dict is strange"
    elif isinstance(pos1, lgsvl.Vector):
        pos1_x = pos1.x
        pos1_z = pos1.z
    elif isinstance(pos1, list) or isinstance(pos1, np.ndarray):
        if len(pos1) == 2:
            pos1_x = pos1[0]
            pos1_z = pos1[1]
        elif len(pos1) == 3:
            pos1_x = pos1[0]
            pos1_z = pos1[2]
        else:
            assert False, "pos1 list is strange"
    else:
        assert False, "pos1 type is not supported"

    if isinstance(pos2, dict):
        if "Position" in pos2:
            pos2_x = pos2["Position"]["x"]
            pos2_z = pos2["Position"]["z"]
        elif "z" in pos2:
            pos2_x = pos2["x"]
            pos2_z = pos2["z"]
        elif "y" in pos2:
            pos2_x = pos2["x"]
            pos2_z = pos2["y"]
        else:
            assert False, "pos2 dict is strange"
    elif isinstance(pos2, lgsvl.Vector):
        pos2_x = pos2.x
        pos2_z = pos2.z
    elif isinstance(pos2, list) or isinstance(pos2, np.ndarray):
        if len(pos2) == 2:
            pos2_x = pos2[0]
            pos2_z = pos2[1]
        elif len(pos2) == 3:
            pos2_x = pos2[0]
            pos2_z = pos2[2]
        else:
            assert False, "pos2 list is strange"
    else:
        assert False, "pos2 type is not supported"

    return ((pos1_x - pos2_x) ** 2 + (pos1_z - pos2_z) ** 2) ** 0.5


def calc_speed(velocity):
    return (velocity["x"] ** 2 + velocity["z"] ** 2) ** 0.5


def get_trace(trace_path):
    with open(trace_path, "r") as f:
        return json.load(f)


def get_ego_states(traces):
    ego_states = []

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

    return ego_states


def get_four_wheel_position(position: dict, rotation: dict) -> list:
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


def get_ego_polygon(position: dict, rotation: dict) -> Polygon:
    ego_wheel = get_four_wheel_position(position, rotation)
    ego_polygon = Polygon(ego_wheel)
    return ego_polygon


def calculate_area_of_ahead(position, rotation, dist: int = 100) -> list:
    wheel = []
    length = 2.835 / 2
    width = 1.66 / 2
    l2 = length * length + width * width
    l = np.sqrt(l2)
    sina = width / l
    degree = np.radians(rotation["y"])
    # degree = rotation

    a = math.asin(sina)
    b = degree
    # x = position[0]
    # y = position[1]
    x = position["x"]
    y = position["z"]

    w1_x = l * np.sin(a + b) + x
    w1_y = l * np.cos(a + b) + y
    wheel.append([w1_x, w1_y])
    w2_x = l * np.sin(b - a) + x
    w2_y = l * np.cos(b - a) + y
    wheel.append([w2_x, w2_y])

    m_x = (w1_x + w2_x) / 2
    m_y = (w1_y + w2_y) / 2

    w3_x = m_x + dist * np.sin(b - math.pi / 4)
    w3_y = m_y + dist * np.cos(b - math.pi / 4)
    wheel.append([w3_x, w3_y])
    w4_x = m_x + dist * np.cos(b - math.pi / 4)
    w4_y = m_y - dist * np.sin(b - math.pi / 4)
    wheel.append([w4_x, w4_y])

    return wheel


def get_junction_area_ahead(position, rotation, map_info, dist: int = 60) -> Polygon:
    ahead_area_polygon = calculate_area_of_ahead(position, rotation, dist)
    ahead_area_polygon = Polygon(ahead_area_polygon)
    junction_list = map_info.areas["junction_areas"]
    res = []
    for key in junction_list:
        points = junction_list[key]
        the_area = Polygon(points)
        if ahead_area_polygon.distance(the_area) == 0:
            res.append(key)
            # print("junction: ", key)
    if len(res) == 0:
        print("no junction ahead!")
        return Polygon()
    elif len(res) == 1:
        return Polygon(map_info.areas["junction_areas"][res[0]])
    else:
        print("multiple junctions!")
        min_dis = 200
        nearest_junction = Polygon()
        for key in res:
            points = junction_list[key]
            the_area = Polygon(points)
            dis = ahead_area_polygon.distance(the_area)
            if dis < min_dis:
                min_dis = dis
                nearest_junction = the_area
        return nearest_junction


def get_crosswalk_area_ahead(position, rotation, osm_map_info, dist: int = 50) -> Polygon:
    ahead_area_polygon = calculate_area_of_ahead(position, rotation, dist)
    ahead_area_polygon = Polygon(ahead_area_polygon)

    res = []
    min_dis = -1
    for crosswalk_id, crosswalk in osm_map_info.crosswalks.items():
        crosswalk_nodes = []
        for node in crosswalk:
            position = [node.position["x"], node.position["z"]]
            crosswalk_nodes.append(position)
        crosswalk_area = Polygon(crosswalk_nodes)
        dis = crosswalk_area.distance(ahead_area_polygon)
        if dis == 0:
            return crosswalk_area
        if dis < min_dis:
            min_dis = dis
            nearest_crosswalk = crosswalk_area

    if min_dis != -1:
        return nearest_crosswalk
    else:
        print("multiple crosswalks!")
        # exit(-1)
        return None


def get_crosswalks_to_pass(route, osm_map_info) -> Polygon:
    res = []
    for crosswalk_id, crosswalk in osm_map_info.crosswalks.items():
        crosswalk_nodes = []
        for node in crosswalk:
            position = [node.position["x"], node.position["z"]]
            crosswalk_nodes.append(Point(position))

        crosswalk_area = unary_union(crosswalk_nodes).convex_hull
        crosswalk_area = Polygon(crosswalk_area)
        if route.intersects(crosswalk_area):
            res.append(crosswalk_area)

    return res


def get_traffic_light_ahead(position, rotation, osm_map_info, dist: int = 50) -> Polygon:
    ahead_area_polygon = calculate_area_of_ahead(position, rotation, dist)
    ahead_area_polygon = Polygon(ahead_area_polygon)
    ego_polygon = get_ego_polygon(position, rotation)

    res = []
    for traffic_light_id, traffic_light in osm_map_info.traffic_lights.items():
        light = traffic_light.nodes[0]

        traffic_light_point = Point(light.position["x"], light.position["z"])
        dis = traffic_light_point.distance(ahead_area_polygon)
        if dis == 0:
            res.append(traffic_light_point)

    min_dis = 200
    nearest_traffic_light = Point()
    for light in res:
        dis = ego_polygon.distance(light)
        if dis < min_dis:
            min_dis = dis
            nearest_traffic_light = light
    return nearest_traffic_light


def get_stop_sign_ahead(position, rotation, map_info, dist: int = 50) -> Polygon:
    ahead_area_polygon = calculate_area_of_ahead(position, rotation, dist)
    ahead_area_polygon = Polygon(ahead_area_polygon)
    ego_polygon = get_ego_polygon(position, rotation)

    res = []
    for element in map_info.get_traffic_sign():
        if element["type"] == "stopsign":
            stop_line_points = [(point["x"], point["z"]) for point in element["stop_line_points"]]
            stop_sign_line = LineString(stop_line_points)
            dis = stop_sign_line.distance(ahead_area_polygon)
            if dis == 0:
                res.append(stop_sign_line)

    min_dis = 200
    nearest_stop_sign = LineString()
    for line in res:
        dis = ego_polygon.distance(line)
        if dis < min_dis:
            min_dis = dis
            nearest_stop_sign = line
    return nearest_stop_sign


def extend_linestring_in_curvilinear(line: LineString, dist: int = 10):
    coords = list(line.coords)

    if len(coords) < 2:
        return line

    dx = coords[0][0] - coords[1][0]
    dy = coords[0][1] - coords[1][1]
    x = coords[0][0] + dist * np.cos(math.atan2(dy, dx))
    y = coords[0][1] + dist * np.sin(math.atan2(dy, dx))
    coords.insert(0, (x, y))

    dx = coords[-1][0] - coords[-2][0]
    dy = coords[-1][1] - coords[-2][1]
    x = coords[-1][0] + dist * np.cos(math.atan2(dy, dx))
    y = coords[-1][1] + dist * np.sin(math.atan2(dy, dx))
    coords.append((x, y))

    return LineString(coords)
