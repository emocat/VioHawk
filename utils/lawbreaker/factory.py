import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), "src"))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from dataparser import scenario
from utils import helper

from EXtraction import ExtractAll
from GeneticAlgorithm import GAGeneration, EncodedTestCase, DecodedTestCase
from AssertionExtraction import SingleAssertion
from utils import map_helper

import testcase_conversion 

import dataparser
import json

class LawBreakerFactory:
    def __init__(self, seed_scenario: scenario.Scenario, trace: str, rule: str) -> None:
        self.scenario = seed_scenario
        self.trace = helper.get_trace(trace)
        self.map_info = map_helper.get_map_info(os.path.join(os.path.dirname(__file__), "../../map/") + "/san_francisco.json")
        
        self.spec = None
        self.output_trace = None
        self.encoded_testcase = None

        self.prepare_spec(rule)
        self.output_trace = testcase_conversion.convert_to_lawbreaker_testcase(self.scenario, self.trace, self.map_info)

    
    def prepare_spec(self, rule: str):
        if rule == "traffic_light_red":
            translated_statement = "(always (((((trafficLightAheadcolor==1) and ((stoplineAhead<=2.0 or junctionAhead<=2.0))) and (not (direction==2)))) -> ((eventually[0,3] (speed<0.5)))))"
            # translated_statement = "(always (((((((trafficLightAheadcolor==1) and ((stoplineAhead<=2.0 or junctionAhead<=2.0))) and (not (direction==2)))) -> ((eventually[0,1] (speed<2.5)))) and (((((((trafficLightAheadcolor==1) and ((stoplineAhead<=2.0 or junctionAhead<=2.0))) and direction==2) and (not PriorityNPCAhead==1)) and (not PriorityPedsAhead==1))) -> ((eventually[0,2] (speed>0.5)))))))"
        elif rule == "traffic_light_yellow":
            # translated_statement = "(always ((((((trafficLightAheadcolor==2) and ((stoplineAhead<=0.0 or (currentLanenumber+1)==0)))) -> ((eventually[0,2] (speed>0.5)))) and ((((((trafficLightAheadcolor==2) and stoplineAhead<=3.5) and (not stoplineAhead<=0.5)) and currentLanenumber>0)) -> ((eventually[0,3] (speed<0.5)))))))"
            translated_statement = "(always ((((((trafficLightAheadcolor==2) and stoplineAhead<=3.5) and (not stoplineAhead<=0.5)) and currentLanenumber>0)) -> ((eventually[0,3] (speed<0.5)))))"
        elif rule == "overtaking":
            translated_statement = "(always ((isOverTaking==1 -> (((turnSignal==1) and ((((eventually[-1,2] (hornOn==1))) or ((((highBeamOn==1 and ((highBeamOn==1 -> ((eventually[0,2] (lowBeamOn==1))))))) or ((lowBeamOn==1 and ((lowBeamOn==1 -> ((eventually[0,2] (highBeamOn==1)))))))))))) and ((eventually[0,10] (((turnSignal==2) and (((((isLaneChanging==1) -> (NearestNPCAhead<=5.0))) and (isLaneChanging==1)))))))))))"
        elif rule == "car_stop_at_crosswalk":
            translated_statement = "(always ((((((crosswalkAhead<=3.0 or junctionAhead<=3.0)) and NPCAheadAhead<=3.0) and (eventually[0,2] (NPCAheadspeed<0.5))) -> (eventually[0,2] (speed<0.5)))))"
        elif rule == "park_at_crosswalk":
            translated_statement = "(always (((crosswalkAhead<=0.1 or junctionAhead <= 0.1) -> (not ((always[0,2] (speed<0.5)))))))"
        elif rule == "park_near_crosswalk":
            translated_statement = "(always (((crosswalkAhead<=6.1 or junctionAhead<=6.1) -> (not ((always[0,2] (speed<0.5)))))))"
        elif rule == "park_near_signal":
            translated_statement = "(always ((signalAhead<=9.14 -> (not ((always[0,2] (speed<0.5)))))))"
        elif rule == "park_near_stop_sign":
            translated_statement = "(always ((stopSignAhead<=9.14 -> (not ((always[0,2] (speed<0.5)))))))"
        elif rule == "pedestrian_at_crosswalk":
            translated_statement = "(always (((junctionAhead<=3.0 and PriorityPedsAhead==1) -> (eventually[0,2] (speed<0.5)))))"
        elif rule == "pedestrian_at_crosswalk_turning_side":
            translated_statement = "(always (((junctionAhead<=3.0 and PriorityPedsAhead==1) -> (eventually[0,2] (speed<0.5)))))"
        else:
            raise ValueError("Rule not supported")

        single_specification = lambda: None
        single_specification.translated_statement = translated_statement
        self.spec = single_specification

    def calc_feedback(self):
        self.encoded_testcase = EncodedTestCase(self.output_trace, self.spec)
        return self.encoded_testcase.fitness
    
    def mutation(self):
        lane_info = self.map_info.get_lane_config()
        crosswalk_info = self.map_info.get_crosswalk_config()

        new_population = [GAGeneration([self.encoded_testcase]).mutation(self.encoded_testcase, lane_info, crosswalk_info)]
        new_encoded_testcase = DecodedTestCase(new_population).decoding()[0]

        new_scenario = testcase_conversion.update_scenario_from_testcase(self.scenario, new_encoded_testcase, self.map_info)
        return new_scenario

    def mutation2(self, tmp_testcase):
        lane_info = self.map_info.get_lane_config()
        crosswalk_info = self.map_info.get_crosswalk_config()

        ga = GAGeneration([self.encoded_testcase])
        p1, p2 = ga.crossover(self.encoded_testcase, tmp_testcase)
        new_population = [ga.mutation(p1, lane_info, crosswalk_info), ga.mutation(p2, lane_info, crosswalk_info)]
        
        new_encoded_testcase = DecodedTestCase(new_population).decoding()[0]

        new_scenario = testcase_conversion.update_scenario_from_testcase(self.scenario, new_encoded_testcase, self.map_info)
        return new_scenario


def get_translated_statement():
    seed = "base.json"
    seed_scenario = dataparser.scenario.scenario_parser(seed)
    ego_position = seed_scenario.elements["ego"][0].transform.position

    extracted_data = ExtractAll("lane_change_in_the_same_road.txt", True)
    origin_case = extracted_data.Get_TestCastINJsonList()
    all_specifications = extracted_data.Get_Specifications()

    scenario_name = origin_case[0]['ScenarioName']
    specifications_in_scenario = all_specifications[scenario_name]
    print("len:", len(specifications_in_scenario))
    first_specification = specifications_in_scenario[0]
    single_specification = SingleAssertion(first_specification, "san_francisco", ego_position)
    print(single_specification.translated_statement)


if __name__ == "__main__":
    scenario = scenario.scenario_parser(sys.argv[1])
    factory = LawBreakerFactory(scenario, sys.argv[2], sys.argv[3])
    print(factory.calc_feedback())
    new_scenario = factory.mutation()
    new_scenario.store("/tmp/tmp.json")