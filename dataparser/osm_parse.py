from dataclasses import dataclass
from enum import Enum
import osmium
from typing import List, Dict, Any


class WayType(Enum):
    STOP_LINE = "stop_line"
    TRAFFIC_LIGHT = "traffic_light"
    LIGHT_BULBS = "light_bulbs"
    LINE_THIN = "line_thin"
    PEDESTRIAN_MARKING = "pedestrian_marking"


@dataclass
class Node:
    id: int
    position: Dict[int, float]


@dataclass
class Element:
    id: int
    nodes: List[Node]


@dataclass
class TrafficLightRelation:
    id: int
    stop_line: Any
    traffic_light: Any
    light_bulbs: Any


class TrafficHandler(osmium.SimpleHandler):
    def __init__(self):
        super(TrafficHandler, self).__init__()
        self.nodes: Dict[int, Node] = dict()
        self.stop_lines: Dict[int, Element] = dict()
        self.traffic_lights: Dict[int, Element] = dict()
        self.light_bulbs: Dict[int, Element] = dict()
        self.pedestrian_marking: Dict[int, Element] = dict()

        self.crosswalks = dict()

        self.traffic_light_relations: List[TrafficLightRelation] = []
        self.solid_white_lines: List[Element] = []
        self.solid_yellow_lines: List[Element] = []
        self.double_yellow_lines: List[Element] = []

    def node(self, n: osmium.Node):
        x = -float(n.tags["y"])
        y = float(n.tags["ele"])
        z = float(n.tags["x"])
        self.nodes[n.id] = Node(n.id, dict(x=x, y=y, z=z))

    def way(self, w: osmium.Way):
        node_list = [self.nodes[node.ref] for node in w.nodes]
        way_type = w.tags.get("type")
        if way_type == WayType.STOP_LINE.value:
            self.stop_lines[w.id] = Element(w.id, node_list)
        elif way_type == WayType.TRAFFIC_LIGHT.value:
            self.traffic_lights[w.id] = Element(w.id, node_list)
        elif way_type == WayType.LIGHT_BULBS.value:
            self.light_bulbs[w.id] = Element(w.id, node_list)
        elif way_type == WayType.PEDESTRIAN_MARKING.value:
            self.pedestrian_marking[w.id] = Element(w.id, node_list)
        elif way_type == WayType.LINE_THIN.value:
            if w.tags["subtype"] == "solid_solid" and w.tags["color"] == "yellow":
                self.double_yellow_lines.append(Element(w.id, node_list))
            elif w.tags["subtype"] == "solid" and w.tags["color"] == "white":
                self.solid_white_lines.append(Element(w.id, node_list))
            elif w.tags["subtype"] == "solid" and w.tags["color"] == "yellow":
                self.solid_yellow_lines.append(Element(w.id, node_list))

    def relation(self, r: osmium.Relation):
        if r.tags["type"] == "regulatory_element" and r.tags["subtype"] == "traffic_light":
            stop_line = traffic_light = light_bulbs = None
            for member in r.members:
                if member.role == "ref_line":
                    stop_line = self.stop_lines[member.ref]
                elif member.role == "traffic_light":
                    traffic_light = self.traffic_lights[member.ref]
                elif member.role == "light_bulbs":
                    light_bulbs = self.light_bulbs[member.ref]
            self.traffic_light_relations.append(TrafficLightRelation(r.id, stop_line, traffic_light, light_bulbs))
        elif r.tags["type"] == "lanelet" and r.tags["subtype"] == "crosswalk":
            crosswalk = []
            for member in r.members:
                if member.type == "w":
                    way = self.pedestrian_marking[member.ref]
                    crosswalk.extend(way.nodes)
            self.crosswalks[r.id] = crosswalk


def osm_parser(file_path: str):
    handler = TrafficHandler()
    handler.apply_file(file_path)
    return handler
