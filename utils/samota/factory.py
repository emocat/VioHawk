import copy
import numpy as np
import os, sys
import json
import math
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), "src/implementation/runner/lib"))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), "src"))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from samota import GS, LS, remove_covered_objs
from utils.samota.src.implementation.runner.lib.utils import evaulate_population_with_archive, generate_adaptive_random_population, update_archive
from RBF import Model as RBF_Model
from utils.samota.src.implementation.runner.lib.candidate import Candidate
from ensemble import ensemble
from pymoo.algorithms.nsga2 import calc_crowding_distance
from pymoo.algorithms.so_genetic_algorithm import GA
from pymoo.factory import get_crossover, get_mutation, get_sampling
from pymoo.model.problem import Problem
from pymoo.optimize import minimize as min_GA
from utils import *
from . import testcase_conversion 
from utils import map_helper

class SamotaFactory:
    def __init__(self, session: str, rule: str) -> None:
        self.session = None
        self.database = []
        self.archive = []
        self.size = 6
        self.lb = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.ub = [0, 0, 0, 2, 2, 2, 2, 2, 2, 3, 7, 0, 5, 0, 0, 0]
        self.threshold_criteria = [0,0,0,0,0.95,0]
        self.no_of_Objectives = 6
        self.g_max = 200
        self.already_executed = []
        self.objective_uncovered = []
        for obj in range(self.no_of_Objectives):
            self.objective_uncovered.append(obj)  # initialising number of uncovered objective

    # def _evaluate(self,x):
    #     fv = x
    #     # DfC_min, DfV_max, DfP_max, DfM_max, DT_max, traffic_lights_max = run_single_scenario(fv)
    #     DfC_min = random.random()
    #     DfV_max = random.random()
    #     DfP_max = random.random()
    #     DfM_max = random.random()
    #     DT_max = random.random()
    #     traffic_lights_max = random.random()

    #     return [DfC_min, DfV_max, DfP_max, DfM_max, DT_max, traffic_lights_max]
    def merge_newdata_into_dataset(self, newdata):
        if self.database is None:
            self.database = newdata
            return newdata
        else:
            self.database.extend(copy.deepcopy(newdata))
            return self.database

    def decode_to_json(self,session,initial_scenario, scenario_code):
        scenario_decoded = testcase_conversion.decode_to_json(session,initial_scenario, scenario_code)
        return scenario_decoded
    
    def calculate_robustness(self,trace_path,scenario):
        with open(trace_path, 'r') as file:
            traces = json.load(file) 
        
        map_path = "~/VioHawk/map/san_francisco.json"
        map_info = map_helper.get_map_info(map_path)
        robustness = testcase_conversion.calculate_robustness(traces,map_info,scenario)
        return robustness

    def prepare_databse_random(self):
        random_population = generate_adaptive_random_population(self.size, self.lb, self.ub)
        return random_population

    def evaulate_population_with_archive(self,trace_path,new_scenario_decoded,new_scenario_candidate):
        if isinstance(new_scenario_candidate, Candidate):
            if new_scenario_candidate.get_candidate_values() not in self.already_executed:
                result = self.calculate_robustness(trace_path,new_scenario_decoded)
                new_scenario_candidate.set_objective_values(result)
                self.already_executed.append(new_scenario_candidate.get_candidate_values())
                return new_scenario_candidate   
        return None

    def Tg_databse(self):
        T_g = GS (self.database,self.objective_uncovered,self.size,self.g_max,self.threshold_criteria,self.lb,self.ub)
        T_g = remove_covered_objs(T_g)
        return T_g
    
    def Tl_databse(self):
        T_l = LS(self.database,self.objective_uncovered,self.size,self.g_max,self.threshold_criteria,self.lb,self.ub)
        return T_l
    
    # def mutate(self):
    #     # def run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger,start,time_budget,database,g_max):
    #     print("Running SAMOTA")
    #     size = self.size
    #     lb = self.lb
    #     ub = self.ub
    #     no_of_Objectives = self.no_of_Objectives
    #     threshold_criteria = self.threshold_criteria
    #     archive = self.archive
    #     already_executed=[]
    #     objective_uncovered = []
    #     database = self.database
    #     g_max = self.g_max

    #     for obj in range(no_of_Objectives):
    #         objective_uncovered.append(obj)  # initialising number of uncovered objective

    #     # random_population = generate_random_population_using_LHS(size, lb, ub)  # Generating random population
    #     random_population =[]

    #     random_population = generate_adaptive_random_population(size, lb, ub)  # Generating random population
    #     print("Random Population:")
    #     for index,seed in enumerate(random_population):
    #         print("Seed"+ str(index))
    #         print(seed.get_candidate_values())
    #         print(seed.get_objective_values())

    #     random_population = evaulate_population_with_archive(self._evaluate, random_population,already_executed)  # evaluating whole generation and storing results
    #     print("Random Population Evaluated")
    #     for index,seed in enumerate(random_population):
    #         print("Seed"+ str(index))
    #         print(seed.get_candidate_values())
    #         print(seed.get_objective_values())

    #     database.extend(copy.deepcopy(random_population))
    #     update_archive(random_population, objective_uncovered, archive, no_of_Objectives,
    #                 threshold_criteria)  # updateing archive
    #     iteration = 0
    #     while(True):
    #         print("Iteration: "+str(iteration))
    #         print("database:")
    #         for index,seed in enumerate(database):
    #             print("database"+ str(index))
    #             print(seed.get_candidate_values())
    #             print(seed.get_objective_values())
    #         T_g = GS (database,objective_uncovered,size,g_max,threshold_criteria,lb,ub)
    #         T_g = remove_covered_objs(T_g)
    #         T_g = evaulate_population_with_archive(self._evaluate, T_g,already_executed)
    #         print("T_g:")
    #         for index,seed in enumerate(T_g):
    #             print("T_g"+ str(index))
    #             print(seed.get_candidate_values())
    #             print(seed.get_objective_values())
    #         update_archive(T_g, objective_uncovered, archive, no_of_Objectives,
    #                     threshold_criteria)
    #         database.extend(T_g)
    #         print("database:")
    #         for index,seed in enumerate(database):
    #             print("database"+ str(index))
    #             print(seed.get_candidate_values())
    #             print(seed.get_objective_values())
    #         T_l = LS(database,objective_uncovered,size,g_max,threshold_criteria,lb,ub)
    #         T_l = evaulate_population_with_archive(self._evaluate, T_l,already_executed)
    #         print("T_l:")
    #         for index,seed in enumerate(T_l):
    #             print("T_l"+ str(index))
    #             print(seed.get_candidate_values())
    #             print(seed.get_objective_values())
    #         update_archive(T_l, objective_uncovered, archive, no_of_Objectives,
    #                     threshold_criteria)
    #         database.extend(T_l)
    #         iteration = iteration + 1
    #         print("database:")
    #         for index,seed in enumerate(database):
    #             print("database"+ str(index))
    #             print(seed.get_candidate_values())
    #             print(seed.get_objective_values())


if __name__ == "__main__":
    session = 1
    rule = "traffic_light_red"
    factory = SamotaFactory(session,rule)
    # factory.mutate()