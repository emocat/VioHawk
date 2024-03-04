"""
dataparser.scenario
"""

"""
Each seed in the corpus refs to a scenario for simulation (and is described by a json file in the corpus dir).
Elements of scenario:
    - Weather
    - Time
    - NPCVehicle
    - Pedestrian
    - Ego Vehicle
    - Traffic Light
    - Static Obstacle
"""
import copy
import abc
import json
import os
from hashlib import md5
from datetime import datetime


# Scenatio Base Classes
class NPCBehaviour:
    def __init__(self, _elementDic=None, **kwargs):
        if _elementDic is not None:
            self.init(_elementDic)

    def init(self, elementDic):
        self.name = elementDic["name"]
        if "parameters" in elementDic:
            self.isLaneChange = elementDic["parameters"]["isLaneChange"]
            self.maxSpeed = elementDic["parameters"]["maxSpeed"]
        else:
            self.isLaneChange = True
            self.maxSpeed = 0

    def to_dic(self):
        resultDic = {}
        resultDic["name"] = self.name
        resultDic["parameters"] = {"isLaneChange": self.isLaneChange, "maxSpeed": self.maxSpeed}
        return resultDic


class Transform:
    def __init__(self, _position, _rotation):
        self.position = _position
        self.rotation = _rotation

    def to_dic(self):
        return {"position": self.position, "rotation": self.rotation}


class WayPoint:
    def __init__(self, _elementDic=None, **kwargs):
        if _elementDic is not None:
            self.init(_elementDic)

    def init(self, elementDic):
        self.ordinalNumber = elementDic["ordinalNumber"]
        self.position = elementDic["position"]
        self.angle = elementDic["angle"]
        self.waitTime = elementDic["waitTime"]
        self.speed = elementDic["speed"]
        if "timestamp" not in elementDic:
            self.timestamp = -1
        else:
            self.timestamp = elementDic["timestamp"]
        if "trigger" not in elementDic:
            self.trigger = dict(effectors=[])
        else:
            self.trigger = elementDic["trigger"]

    def to_dic(self):
        resultDic = {}
        resultDic["ordinalNumber"] = self.ordinalNumber
        resultDic["position"] = self.position
        resultDic["angle"] = self.angle
        resultDic["waitTime"] = self.waitTime
        resultDic["speed"] = self.speed
        if self.timestamp != -1:
            resultDic["timestamp"] = self.timestamp
        resultDic["trigger"] = self.trigger
        return resultDic


class ControlPolicy:
    def __init__(self, _action, _value):
        self.action = _action
        self.value = _value

    def to_dic(self):
        return {"action": self.action, "value": str(self.value)}


# Scenatio Element Classes
class ElementBase(metaclass=abc.ABCMeta):
    def __init__(self, **kwargs):
        self.uid = kwargs["uid"]

    @abc.abstractmethod
    def to_dic(self):
        return {"uid": self.uid}


class NPCVehicle(ElementBase):
    def __init__(self, _elementDic=None, **kwargs):
        self.name = "npc"
        if _elementDic is not None:
            self.init(_elementDic)

    def init(self, elementDic):
        super().__init__(uid=elementDic["uid"])
        self.variant = elementDic["variant"]
        self.parameterType = elementDic["parameterType"]
        self.transform = Transform(elementDic["transform"]["position"], elementDic["transform"]["rotation"])
        self.color = elementDic["color"]
        self.behaviour = NPCBehaviour(_elementDic=elementDic["behaviour"])
        self.wayPoints = []
        for wayPoint in elementDic["waypoints"]:
            self.wayPoints.append(WayPoint(_elementDic=wayPoint))

    def to_dic(self):
        resultDic = super().to_dic()
        resultDic["variant"] = self.variant
        resultDic["type"] = 2
        resultDic["parameterType"] = self.parameterType
        resultDic["transform"] = self.transform.to_dic()
        resultDic["behaviour"] = self.behaviour.to_dic()
        resultDic["color"] = self.color
        wayPointArray = []
        for wayPoint in self.wayPoints:
            wayPointArray.append(wayPoint.to_dic())
        resultDic["waypoints"] = wayPointArray
        return resultDic


class Pedestrian(ElementBase):
    def __init__(self, _elementDic=None, **kwargs):
        self.name = "pedestrian"
        if _elementDic is not None:
            self.init(_elementDic)

    def init(self, elementDic):
        super().__init__(uid=elementDic["uid"])
        self.variant = elementDic["variant"]
        self.parameterType = elementDic["parameterType"]
        self.transform = Transform(elementDic["transform"]["position"], elementDic["transform"]["rotation"])
        self.wayPoints = []
        for wayPoint in elementDic["waypoints"]:
            self.wayPoints.append(WayPoint(_elementDic=wayPoint))

    def to_dic(self):
        resultDic = super().to_dic()
        resultDic["variant"] = self.variant
        resultDic["type"] = 3
        resultDic["parameterType"] = self.parameterType
        resultDic["transform"] = self.transform.to_dic()
        wayPointArray = []
        for wayPoint in self.wayPoints:
            wayPointArray.append(wayPoint.to_dic())
        resultDic["waypoints"] = wayPointArray
        return resultDic


class Weather(ElementBase):
    def __init__(self, _elementDic=None, **kwargs):
        self.name = "weather"
        if _elementDic is not None and "rain" in _elementDic:
            self.init(_elementDic)
        else:
            self.init_weather()

    def init(self, elementDic):
        self.rain = elementDic["rain"]
        self.fog = elementDic["fog"]
        self.wetness = elementDic["wetness"]
        self.cloudiness = elementDic["cloudiness"]
        self.damage = elementDic["damage"]

    def init_weather(self):
        self.rain = 0
        self.fog = 0
        self.wetness = 0
        self.cloudiness = 0
        self.damage = 0

    def to_dic(self):
        resultDic = {}
        resultDic["rain"] = self.rain
        resultDic["fog"] = self.fog
        resultDic["wetness"] = self.wetness
        resultDic["cloudiness"] = self.cloudiness
        resultDic["damage"] = self.damage
        return resultDic


class Time(ElementBase):
    def __init__(self, _elementDic=None, **kwargs):
        self.name = "time"
        if _elementDic is not None and "year" in _elementDic:
            self.init(_elementDic)
        else:
            self.init_curr_time()

    def init(self, elementDic):
        self.year = elementDic["year"]
        self.month = elementDic["month"]
        self.day = elementDic["day"]
        self.hour = elementDic["hour"]
        self.minute = elementDic["minute"]
        self.second = elementDic["second"]

    def init_curr_time(self):
        dt = datetime.now()
        self.year = dt.year
        self.month = dt.month
        self.day = dt.day
        self.hour = dt.hour
        self.minute = dt.minute
        self.second = dt.second

    def to_dic(self):
        resultDic = {}
        resultDic["year"] = self.year
        resultDic["month"] = self.month
        resultDic["day"] = self.day
        resultDic["hour"] = self.hour
        resultDic["minute"] = self.minute
        resultDic["second"] = self.second
        return resultDic


class EgoVehicle(ElementBase):
    def __init__(self, _elementDic=None, **kwargs):
        self.name = "ego"
        if _elementDic is not None:
            self.init(_elementDic)

    def init(self, elementDic):
        super().__init__(uid=elementDic["uid"])
        self.id = elementDic["id"]
        self.variant = elementDic["variant"]
        self.parameterType = elementDic["parameterType"]
        self.transform = Transform(elementDic["transform"]["position"], elementDic["transform"]["rotation"])
        if "initial_speed" in elementDic:
            self.initial_speed = elementDic["initial_speed"]
        self.sensorsConfigurationId = elementDic["sensorsConfigurationId"]
        self.destination = None
        if "destinationPoint" in elementDic:
            self.destination = Transform(
                elementDic["destinationPoint"]["position"], elementDic["destinationPoint"]["rotation"]
            )

    def to_dic(self):
        resultDic = {}
        resultDic["id"] = self.id
        resultDic["uid"] = self.uid
        resultDic["variant"] = self.variant
        resultDic["type"] = 1
        resultDic["parameterType"] = self.parameterType
        resultDic["transform"] = self.transform.to_dic()
        if hasattr(self, "initial_speed"):
            resultDic["initial_speed"] = self.initial_speed
        resultDic["sensorsConfigurationId"] = self.sensorsConfigurationId
        if self.destination is not None:
            resultDic["destinationPoint"] = self.destination.to_dic()
        return resultDic


class TrafficLight(ElementBase):
    def __init__(self, _elementDic=None, **kwargs):
        self.name = "trafficlight"
        if _elementDic is not None:
            self.init(_elementDic)

    def init(self, elementDic):
        super().__init__(uid=elementDic["uid"])
        self.spawned = elementDic["spawned"]
        self.policies = []
        self.transform = None
        for policy in elementDic["policy"]:
            self.policies.append(ControlPolicy(policy["action"], policy["value"]))
        if self.spawned:
            self.transform = Transform(elementDic["transform"]["position"], elementDic["transform"]["rotation"])

    def to_dic(self):
        resultDic = super().to_dic()
        policyArray = []
        for policy in self.policies:
            policyArray.append(policy.to_dic())
        resultDic["policy"] = policyArray
        resultDic["spawned"] = self.spawned
        if self.spawned:
            resultDic["transform"] = self.transform.to_dic()
        return resultDic


class StaticObstacle(ElementBase):
    def __init__(self, _elementDic=None, **kwargs):
        self.name = "obstacle"
        if _elementDic is not None:
            self.init(_elementDic)

    def init(self, elementDic):
        super().__init__(uid=elementDic["uid"])
        self.type = elementDic["name"]
        self.spawned = elementDic["spawned"]
        self.policies = []
        self.transform = None
        for policy in elementDic["policy"]:
            self.policies.append(ControlPolicy(policy["action"], policy["value"]))
        if self.spawned:
            self.transform = Transform(elementDic["transform"]["position"], elementDic["transform"]["rotation"])

    def to_dic(self):
        resultDic = super().to_dic()
        policyArray = []
        for policy in self.policies:
            policyArray.append(policy.to_dic())
        resultDic["policy"] = policyArray
        resultDic["spawned"] = self.spawned
        resultDic["name"] = self.type
        if self.spawned:
            resultDic["transform"] = self.transform.to_dic()
        return resultDic


class Scenario:
    def __init__(self, _seed_path=None, _elements=None):
        self.seed_path = None
        self.elements = {}
        # json obj refers to the scenario
        self.json_obj = None
        self.hash = None
        if _elements is not None:
            self.elements = copy.deepcopy(_elements)
        elif _seed_path is not None:
            self.seed_path = _seed_path
            self.from_json()
        self.verified = False
        # the score is determined by the feedback function
        self.score = 0.0

    def __lt__(self, scene):
        return self.score < scene.score

    def __le__(self, scene):
        return self.score <= scene.score

    def from_json(self):
        assert (self.json_obj is None) and (self.seed_path is not None)
        self.json_obj = json.load(open(self.seed_path, encoding="utf-8"))
        self.reset_elements()
        # Variables that do not need to be mutated
        self.version = self.json_obj["version"]
        if "vseMetadata" in self.json_obj:
            self.vseMetadata = self.json_obj["vseMetadata"]
        else:
            self.vseMetadata = dict()
        if "weather" not in self.json_obj:
            self.add_element(Weather())
        else:
            self.add_element(Weather(_elementDic=self.json_obj["weather"]))
        if "time" not in self.json_obj:
            self.add_element(Time())
        else:
            self.add_element(Time(_elementDic=self.json_obj["time"]))
        self.map = self.json_obj["map"]
        for agent in self.json_obj["agents"]:
            if agent["type"] == 1:
                self.add_element(EgoVehicle(_elementDic=agent))
            elif agent["type"] == 2:
                self.add_element(NPCVehicle(_elementDic=agent))
            elif agent["type"] == 3:
                self.add_element(Pedestrian(_elementDic=agent))

        for controllable in self.json_obj["controllables"]:
            if "name" in controllable:
                self.add_element(StaticObstacle(controllable))
            else:
                self.add_element(TrafficLight(controllable))

    def reset_elements(self):
        self.elements = {}
        self.elements["weather"] = []
        self.elements["time"] = []
        self.elements["ego"] = []
        self.elements["npc"] = []
        self.elements["pedestrian"] = []
        self.elements["trafficlight"] = []
        self.elements["obstacle"] = []

    def add_element(self, element):
        if element.name in self.elements:
            self.elements[element.name].append(element)
        else:
            self.elements[element.name] = [element]

    def store(self, _store_path):
        if self.json_obj is None:
            self.to_json()
        # write it to the _store_path
        with open(_store_path, "w", encoding="utf-8") as f:
            json.dump(self.json_obj, f, indent=4)

    def to_json(self):
        # convert elements(self.elements) to json obj
        self.json_obj = {}
        agents = []
        controllables = []
        agents.extend([element.to_dic() for element in self.elements["ego"]])
        if len(self.elements["npc"]) > 0:
            agents.extend([element.to_dic() for element in self.elements["npc"]])
        if len(self.elements["pedestrian"]) > 0:
            agents.extend([element.to_dic() for element in self.elements["pedestrian"]])
        # add controllables
        if len(self.elements["trafficlight"]) > 0:
            controllables.extend([element.to_dic() for element in self.elements["trafficlight"]])
        if len(self.elements["obstacle"]) > 0:
            controllables.extend([element.to_dic() for element in self.elements["obstacle"]])
        self.json_obj["seed_path"] = self.seed_path
        self.json_obj["version"] = self.version
        self.json_obj["vseMetadata"] = self.vseMetadata
        self.json_obj["weather"] = self.elements["weather"][0].to_dic()
        self.json_obj["time"] = self.elements["time"][0].to_dic()
        self.json_obj["map"] = self.map
        self.json_obj["agents"] = agents
        self.json_obj["controllables"] = controllables

        return self.json_obj

    def get_hash(self):
        # for efficient scenario deduplication
        if self.hash == None:
            if self.json_obj == None:
                self.to_json()
            self.hash = md5(json.dumps(self.json_obj, indent=4).encode()).hexdigest()
        return self.hash


def scenario_parser(_seed):
    """
    Return a scenario object which contains all elements(e.g., NPC, ENV, TIME, EGO ...) in the scenario.
    Args:
        _seed (file_path): The json file of the seed.
    Returns:
        object that refers to the scenario (class Scenario)
    """
    scenario = Scenario(_seed)
    return scenario


def corpus_parser(_seeds):
    """
    Return a list of scenario objects for json files in the corpus directory
    Args:
        _seeds (dir_path): The corpus directory
    Returns:
        list of scenario objects
    """
    corpus = []
    # for file in seeds: corpus.append(scenario_parse(file))
    for file in os.listdir(_seeds):
        if file.endswith(".json"):
            corpus.append(scenario_parser(os.path.join(_seeds, file)))
    return corpus
