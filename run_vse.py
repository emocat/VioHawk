#!/usr/bin/env python3
#
# Copyright (c) 2020-2021 LG Electronics, Inc.
#
# This software contains code licensed as described in LICENSE.
#

import json
import logging
import os
import re
import sys
import math
import time
from datetime import datetime

import config

# import logger
import dataparser

# LOG = logger.get_logger(config.__prog__)

import lgsvl
import timeout_decorator

FORMAT = "%(asctime)-15s [%(levelname)s][%(module)s] %(message)s"

logging.basicConfig(level=logging.INFO, format=FORMAT)
log = logging.getLogger(__name__)


class MyException(Exception):
    pass


class VSERunner:
    def __init__(self, _seed: dataparser.scenario.Scenario, _sensor_conf: str = None):
        self.seed = _seed
        self.VSE_dict = _seed.to_json()
        self.sim = None
        self.ego_agents = []
        self.npc_agents = []
        self.npc_count = 0
        self.pedestrian_agents = []
        self.collision_object = set()
        self.collision_object_detail = []
        self.maxint = 130
        self.is_collision = False
        self.sensor_conf = _sensor_conf

        self.start_time = 0
        self.collision_time = 0

    def reset(self):
        log.debug("Reset VSE runner")
        self.ego_agents.clear()
        self.npc_agents.clear()
        self.pedestrian_agents.clear()

    def close(self):
        self.reset()
        self.sim.reset()
        self.sim.close()

    def setup_sim(self, default_host="127.0.0.1", default_port=8181):
        if not self.sim:
            simulator_host = os.getenv("LGSVL__SIMULATOR_HOST", default_host)
            simulator_port = int(os.getenv("LGSVL__SIMULATOR_PORT", default_port))
            log.debug("simulator_host is {}, simulator_port is {}".format(simulator_host, simulator_port))
            self.sim = lgsvl.Simulator(simulator_host, simulator_port)

    def connect_bridge(self, ego_agent, ego_index=0, default_host="127.0.0.1", default_port=9090):
        autopilot_host_env = "LGSVL__AUTOPILOT_{}_HOST".format(ego_index)
        autopilot_port_env = "LGSVL__AUTOPILOT_{}_PORT".format(ego_index)
        bridge_host = os.environ.get(autopilot_host_env, default_host)
        bridge_port = int(os.environ.get(autopilot_port_env, default_port))
        ego_agent.connect_bridge(bridge_host, bridge_port)

        return bridge_host, bridge_port

    def load_scene(self):
        if "map" not in self.VSE_dict.keys():
            log.error("No map specified in the scenario.")
            # sys.exit(1)
            raise MyException

        scene = self.VSE_dict["map"]["name"]
        log.info("Loading {} map.".format(scene))
        if self.sim.current_scene == scene:
            self.sim.reset()
        else:
            self.sim.load(scene, seed=650387)
        log.info("Loaded.")

    def load_agents(self):
        if "agents" not in self.VSE_dict.keys():
            log.warning("No agents specified in the scenario")
            return

        agents_data = self.VSE_dict["agents"]
        for agent_data in agents_data:
            log.debug("Adding agent {}, type: {}".format(agent_data["variant"], agent_data["type"]))
            agent_type_id = agent_data["type"]
            if agent_type_id == lgsvl.AgentType.EGO.value:
                self.ego_agents.append(agent_data)

            elif agent_type_id == lgsvl.AgentType.NPC.value:
                self.npc_agents.append(agent_data)

            elif agent_type_id == lgsvl.AgentType.PEDESTRIAN.value:
                self.pedestrian_agents.append(agent_data)

            else:
                log.warning("Unsupported agent type {}. Skipping agent.".format(agent_data["type"]))

        self.npc_count = len(self.npc_agents)
        log.info("Loaded {} ego agents".format(len(self.ego_agents)))
        log.info("Loaded {} NPC agents".format(len(self.npc_agents)))
        log.info("Loaded {} pedestrian agents".format(len(self.pedestrian_agents)))

    def set_weather(self):
        if "weather" not in self.VSE_dict.keys() or "rain" not in self.VSE_dict["weather"]:
            log.debug("No weather specified in the scenarios")
            return
        weather_data = self.VSE_dict["weather"]
        weather_state = lgsvl.WeatherState(
            rain=weather_data["rain"],
            fog=weather_data["fog"],
            wetness=weather_data["wetness"],
            cloudiness=weather_data["cloudiness"],
            damage=weather_data["damage"],
        )
        self.sim.weather = weather_state

    def set_time(self):
        if "time" not in self.VSE_dict.keys() or "year" not in self.VSE_dict["time"]:
            log.debug("No time specified in the scenarios")
            return
        time_data = self.VSE_dict["time"]
        dt = datetime(
            year=time_data["year"],
            month=time_data["month"],
            day=time_data["day"],
            hour=time_data["hour"],
            minute=time_data["minute"],
            second=time_data["second"],
        )
        self.sim.set_date_time(dt, fixed=False)

    def add_controllables(self):
        if "controllables" not in self.VSE_dict.keys():
            log.debug("No controllables specified in the scenarios")
            return

        controllables_data = self.VSE_dict["controllables"]
        for controllable_data in controllables_data:
            # Name checking for backwards compability
            spawned = "name" in controllable_data or ("spawned" in controllables_data and controllable_data["spawned"])
            if spawned:
                log.debug("Adding controllable {}".format(controllable_data["name"]))
                controllable_state = lgsvl.ObjectState()
                controllable_state.transform = self.read_transform(controllable_data["transform"])
                try:
                    controllable = self.sim.controllable_add(controllable_data["name"], controllable_state)
                    controllable.attr = controllable_state.transform.position.x
                    policy = controllable_data["policy"]
                    if len(policy) > 0:
                        controllable.control(policy)
                except Exception as e:
                    msg = "Failed to add controllable {}, please make sure you have the correct simulator".format(
                        controllable_data["name"]
                    )
                    log.error(msg)
                    log.error("Original exception: " + str(e))
            else:
                uid = controllable_data["uid"]
                policy = controllable_data["policy"]
                if len(policy) > 0:
                    log.debug("Setting policy for controllable {}".format(uid))
                    controllable = self.sim.get_controllable_by_uid(uid)
                    controllable.control(policy)

    def add_ego(self):
        for i, agent in enumerate(self.ego_agents):
            if "id" in agent:
                agent_name = agent["id"]
            else:
                agent_name = agent["variant"]
            agent_state = lgsvl.AgentState()
            if "initial_speed" in agent:
                agent_state.velocity = lgsvl.Vector(
                    agent["initial_speed"]["x"], agent["initial_speed"]["y"], agent["initial_speed"]["z"]
                )
            agent_state.transform = self.read_transform(agent["transform"])
            if "destinationPoint" in agent:
                agent_destination = lgsvl.Vector(
                    agent["destinationPoint"]["position"]["x"],
                    agent["destinationPoint"]["position"]["y"],
                    agent["destinationPoint"]["position"]["z"],
                )
                #
                # Set distination rotation once it is supported by DreamView
                #
                agent_destination_rotation = lgsvl.Vector(
                    agent["destinationPoint"]["rotation"]["x"],
                    agent["destinationPoint"]["rotation"]["y"],
                    agent["destinationPoint"]["rotation"]["z"],
                )

            def _on_collision(agent1, agent2, contact):
                self.is_collision = True
                self.collision_time = time.time() - self.start_time
                name1 = "STATIC OBSTACLE" if agent1 is None else agent1.name
                name2 = "STATIC OBSTACLE" if agent2 is None else agent2.name
                # LOG.debug("{} collided with {} at {} in {}s".format(name1, name2, contact, self.collision_time))
                log.info("{} collided with {} at {} in {}s".format(name1, name2, contact, self.collision_time))
                # self.seed.store(self.workdir + "/collision/" + str(self.seed.get_hash()))
                if agent1 is None or agent2 is None:
                    pass
                else:
                    self.collision_object.add(agent1.attr)
                    self.collision_object.add(agent2.attr)

                if name1 == agent["sensorsConfigurationId"]:
                    _ego, _npc = agent1, agent2
                else:
                    _ego, _npc = agent2, agent1
                st1 = _ego.state
                st2 = _npc.state if _npc is not None else None

                if st2 is not None:
                    degree = abs(st1.rotation.y - st2.rotation.y)
                    degree = degree if degree < 180 else 360 - degree
                    # if st1.speed < st2.speed and degree <= 90:
                    #     log.info("NPC rear-end collision")
                    # elif st1.speed > st2.speed and degree <= 90:
                    #     log.info("EGO rear-end collision")
                    # else:
                    #     log.info("head-on collision")
                    log.info("ego speed: {} m/s".format(st1.speed))
                    log.info("npc speed: {} m/s".format(st2.speed))
                    log.info("collision degree: {}".format(degree))
                    log.info("collision time: {}".format(self.collision_time))

                self.collision_object_detail = [st1, st2, self.collision_time]

                log.info("Stopping simulation")
                self.sim.stop()

            try:
                log.info(self.sensor_conf)
                if self.sensor_conf:
                    ego = self.sim.add_agent(self.sensor_conf, lgsvl.AgentType.EGO, agent_state)
                elif "sensorsConfigurationId" in agent:
                    ego = self.sim.add_agent(agent["sensorsConfigurationId"], lgsvl.AgentType.EGO, agent_state)
                else:
                    ego = self.sim.add_agent(agent_name, lgsvl.AgentType.EGO, agent_state)
                ego.attr = agent_state.transform.position.x
                ego.on_collision(_on_collision)
            except Exception as e:
                msg = "Failed to add agent {}, please make sure you have the correct simulator".format(agent_name)
                log.error(msg)
                log.error("Original exception: " + str(e))
                # sys.exit(1)
                raise MyException

            try:
                bridge_host = self.connect_bridge(ego, i)[0]

                default_modules = [
                    "Localization",
                    "Transform",
                    "Routing",
                    "Prediction",
                    "Planning",
                    "Control",
                ]

                if self.sensor_conf in [
                    "0a11578a-db19-40a6-90bd-9efcf655a503",
                    "88d81ce0-bcc9-47fc-8a39-50fb368e8c06",
                    "fd2d5a15-8a6f-4c0d-a238-9478f3a91031",
                    "151ff968-ed16-4dde-a30c-f8d5cf760b82",
                ]:
                    default_modules.append("Perception")

                try:
                    modules = os.environ.get("LGSVL__AUTOPILOT_{}_VEHICLE_MODULES".format(i)).split(",")
                    if len(modules) == 0:
                        modules = default_modules
                except Exception:
                    modules = default_modules
                dv = lgsvl.dreamview.Connection(self.sim, ego, bridge_host)

                hd_map = os.environ.get("LGSVL__AUTOPILOT_HD_MAP")
                if not hd_map:
                    hd_map = self.sim.current_scene
                    words = self.split_pascal_case(hd_map)
                    hd_map = " ".join(words)

                if dv.get_current_map().replace(" ", "_") != hd_map.replace(" ", "_"):
                    log.info("First run")
                    tmp_st = dv.ego.state
                    tmp_st.velocity = lgsvl.Vector(0, 0, 0)
                    dv.ego.state = tmp_st

                dv.set_hd_map(hd_map)
                dv.set_vehicle(os.environ.get("LGSVL__AUTOPILOT_{}_VEHICLE_CONFIG".format(i), agent["variant"]))
                if "destinationPoint" in agent:
                    dv.setup_apollo(agent_destination.x, agent_destination.z, modules)
                else:
                    log.info("No destination set for EGO {}".format(agent_name))
                    dv.setup_apollo(agent_state.position.x, agent_state.position.z, modules)
                    # for mod in modules:
                    #     dv.enable_module(mod)
            except RuntimeWarning as e:
                msg = "Skipping bridge connection for vehicle: {}".format(agent["id"])
                log.warning("Original exception: " + str(e))
                log.warning(msg)
            except Exception as e:
                msg = "Something went wrong with bridge / dreamview connection."
                log.error("Original exception: " + str(e))
                log.error(msg)
                raise MyException

    def add_npc(self):
        for agent in self.npc_agents:
            if "id" in agent:
                agent_name = agent["id"]
            else:
                agent_name = agent["variant"]
            agent_state = lgsvl.AgentState()
            agent_state.transform = self.read_transform(agent["transform"])
            agent_color = (
                lgsvl.Vector(agent["color"]["r"], agent["color"]["g"], agent["color"]["b"])
                if "color" in agent
                else None
            )

            try:
                npc = self.sim.add_agent(agent_name, lgsvl.AgentType.NPC, agent_state, agent_color)
                npc.attr = agent_state.transform.position.x
            except Exception as e:
                msg = "Failed to add agent {}, please make sure you have the correct simulator".format(agent_name)
                log.error(msg)
                log.error("Original exception: " + str(e))
                raise MyException

            if agent["behaviour"]["name"] == "NPCWaypointBehaviour":
                waypoints = self.read_waypoints(agent["waypoints"])
                if waypoints:
                    npc.follow(waypoints)
            elif agent["behaviour"]["name"] == "NPCLaneFollowBehaviour":
                maxSpeed = agent["behaviour"]["parameters"]["maxSpeed"]
                if maxSpeed == 0:
                    maxSpeed = 0.000001
                npc.follow_closest_lane(True, maxSpeed, agent["behaviour"]["parameters"]["isLaneChange"])

    def add_pedestrian(self):
        for agent in self.pedestrian_agents:
            if "id" in agent:
                agent_name = agent["id"]
            else:
                agent_name = agent["variant"]
            agent_state = lgsvl.AgentState()
            agent_state.transform = self.read_transform(agent["transform"])

            try:
                pedestrian = self.sim.add_agent(agent_name, lgsvl.AgentType.PEDESTRIAN, agent_state)
                pedestrian.attr = agent_state.transform.position.x
            except Exception as e:
                msg = "Failed to add agent {}, please make sure you have the correct simulator".format(agent_name)
                log.error(msg)
                log.error("Original exception: " + str(e))
                # sys.exit(1)
                raise MyException

            waypoints = self.read_waypoints(agent["waypoints"])
            if waypoints:
                pedestrian.follow(waypoints)

    def read_transform(self, transform_data):
        transform = lgsvl.Transform()
        transform.position = lgsvl.Vector.from_json(transform_data["position"])
        transform.rotation = lgsvl.Vector.from_json(transform_data["rotation"])

        return transform

    def read_waypoints(self, waypoints_data):
        waypoints = []
        for waypoint_data in waypoints_data:
            position = lgsvl.Vector.from_json(waypoint_data["position"])
            speed = waypoint_data["speed"]
            angle = lgsvl.Vector.from_json(waypoint_data["angle"])
            if "wait_time" in waypoint_data:
                wait_time = waypoint_data["wait_time"]
            elif "waitTime" in waypoint_data:
                wait_time = waypoint_data["waitTime"]
            else:
                wait_time = 0.0
            trigger = self.read_trigger(waypoint_data)
            if "timestamp" in waypoint_data:
                timestamp = waypoint_data["timestamp"]
            else:
                timestamp = -1

            if "trigger_distance" in waypoint_data:
                td = waypoint_data["trigger_distance"]
                waypoint = lgsvl.DriveWaypoint(
                    position,
                    speed,
                    angle=angle,
                    idle=wait_time,
                    trigger_distance=td,
                    timestamp=timestamp,
                    trigger=trigger,
                )
            else:
                waypoint = lgsvl.DriveWaypoint(
                    position, speed, angle=angle, idle=wait_time, timestamp=timestamp, trigger=trigger
                )

            waypoints.append(waypoint)

        return waypoints

    def read_trigger(self, waypoint_data):
        if "trigger" not in waypoint_data:
            return None
        effectors_data = waypoint_data["trigger"]["effectors"]
        if len(effectors_data) == 0:
            return None

        effectors = []
        for effector_data in effectors_data:
            effector = lgsvl.TriggerEffector(effector_data["typeName"], effector_data["parameters"])
            effectors.append(effector)
        trigger = lgsvl.WaypointTrigger(effectors)

        return trigger

    def split_pascal_case(self, s):
        matches = re.finditer(".+?(?:(?<=[a-z])(?=[A-Z\d])|(?<=[A-Z\d])(?=[A-Z][a-z])|$)", s)
        return [m.group(0) for m in matches]

    @timeout_decorator.timeout(180)
    def run(self, duration=0.0, force_duration=False, loop=False):
        log.debug("Duration is set to {}.".format(duration))
        self.setup_sim()

        try:
            while True:
                self.load_scene()
                self.load_agents()
                self.set_weather()
                self.set_time()
                self.add_ego()
                self.add_npc()
                self.add_pedestrian()
                self.add_controllables()

                log.info("Starting scenario...")
                self.start_time = time.time()
                self.sim.run(duration)
                log.info("Scenario simulation ended.")

                if loop:
                    self.reset()
                else:
                    break
        except MyException:
            log.error("Program exit!")
            exit(-1)

        self.close()
