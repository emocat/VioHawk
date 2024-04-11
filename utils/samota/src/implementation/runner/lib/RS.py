import copy
import time
from utils import *
import copy
import time

from utils import *


def run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger,start,time_budget):

    threshold_criteria = criteria
    objective_uncovered = []
    for obj in range(no_of_Objectives):
        objective_uncovered.append(obj)  # initialising number of uncovered objective
    while True:
        random_population = generate_random_population(size, lb, ub)  # Generating random population
        P_T = copy.copy(random_population)
        evaulate_population(func, random_population)  # evaluating whole generation and storing results

        update_archive(random_population, objective_uncovered, archive, no_of_Objectives,
                       threshold_criteria)  # updating archive
        for arc in archive:
            logger.info("***ARCHIVE***")
            logger.info("\nValues: " + str(
                arc.get_candidate_values()) + "\nwith objective values: " + str(
                arc.get_objective_values()) + "\nSatisfying Objective: " + str(
                arc.get_covered_objectives()))

def minimize(func, size, lb, ub, no_of_Objectives, criteria,time_budget,logger,archive):
    assert hasattr(func, '__call__')

    start = time.time()
    run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger,start,time_budget)



