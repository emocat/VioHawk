import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import copy
import random

from dataparser import scenario
from utils import helper
from utils.map_helper import get_map_info

class AVFuzzerFactory:
    def __init__(self, seed_scenario: scenario.Scenario, trace: str, rule: str) -> None:
        self.scenario = seed_scenario
        self.trace = helper.get_trace(trace)
        
    def calc_feedback(self):
        minD = 130
        for trace in self.trace:
            ego_position = trace["EGO"]["Position"]
            for npc in trace["NPCs"]:
                npc_position = npc["Position"]
                curD = helper.calc_distance(ego_position, npc_position)

                if minD > curD:
                    minD = curD

        # As the map is not all straight lane scenario, we don't calculate delta distance
        # fitness = -1 * minD
        fitness = minD
        score = fitness
        # score = (fitness + self.maxint) / float(len(self.npc_agents) - 1)
        return score

    def mutation(self):
        bounds = [[0, 3], [0, 3]]
        
        new_scenario = copy.deepcopy(self.scenario)
        new_scenario.hash = None
        new_scenario.json_obj = None

        for npc in new_scenario.elements["npc"]:
            if npc.behaviour.name == "NPCLaneFollowBehaviour":
                npc.behaviour.maxSpeed = random.uniform(bounds[0][0], bounds[0][1])
                npc.behaviour.isLaneChange = random.choice([True, False])
            else:
                raise Exception("Unknown NPC behaviour: {}".format(npc.behaviour.name))

        return new_scenario

