import sys
import copy
import numpy
import time
import multiprocessing
import time
import numpy as np
from pymoo.algorithms.nsga2 import calc_crowding_distance
from candidate import Candidate
from utils import *

# finding best candidates and assigning to each front
def fast_dominating_sort(R_T, objective_uncovered):
    to_return = []
    front = []
    count = 0
    while len(R_T) > 1:
        count = 0
        for outer_loop in range(len(R_T)):
            best = R_T[outer_loop]
            add = True
            for inner_loop in range(len(R_T)):
                against = R_T[inner_loop]
                if best == against:
                    continue
                if (dominates(best.get_objective_values(), against.get_objective_values(), objective_uncovered)):
                    continue
                else:
                    add = False
                    break

            if add == True:
                if best not in front:
                    front.append(best)

                count = count + 1

        if len(front) > 0:
            to_return.append(front)
            for i in range(len(front)):
                R_T.remove(front[i])
                front = []

        if (len(to_return) == 0) or (count == 0):  # to check if no one dominates no one
            to_return.append(R_T)
            break

    return to_return


# sorting based on crowding distance
def sort_based_on_crowding_distance(e):
    values = e.get_crowding_distance()
    return values


def sort_based_on(e):
    values = e.get_objective_values()
    return values[0]


# sorting based on first objective value
def sort_worse(pop):
    pop.sort(key=sort_based_on, reverse=True)
    return pop
# preference sort, same as algorithm
def preference_sort(R_T, size, objective_uncovered):
    to_return = []
    for objective_index in objective_uncovered:
        min = 100
        best = R_T[0]
        for index in range(len(R_T)):
            objective_values = R_T[index].get_objective_values()
            if objective_values[objective_index] < min:
                min = objective_values[objective_index]
                best = R_T[index]
        to_return.append(best)
        R_T.remove(best)
    if len(R_T)>0:
        E = fast_dominating_sort(R_T, objective_uncovered)
        for i in range(len(E)):
            to_return.append(E[i])
    return to_return


# converting to numpy array (Required by library)
def get_array_for_crowding_distance(sorted_front):
    list = []
    for value in sorted_front:
        objective_values = value.get_objective_values()

        np_array = numpy.array(objective_values)
        list.append(np_array)

    np_list = np.array(list)
    cd = calc_crowding_distance(np_list)
    return cd
# method to assign each candidate its crownding distance

def assign_crowding_distance_to_each_value(sorted_front, crowding_distance):
    for candidate_index in range(len(sorted_front)):
        objective_values = sorted_front[candidate_index]
        objective_values.set_crowding_distance(crowding_distance[candidate_index])

def run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger,start,time_budget):

    threshold_criteria = criteria

    objective_uncovered = []
    # func("test")

    for obj in range(no_of_Objectives):
        objective_uncovered.append(obj)  # initialising number of uncovered objective

    random_population = generate_random_population(size, lb, ub)  # Generating random population
    P_T = copy.copy(random_population)
    evaulate_population(func, random_population)  # evaluating whole generation and storing results
    print(random_population[0].get_objective_values())
    update_archive(random_population, objective_uncovered, archive, no_of_Objectives,
                   threshold_criteria)  # updateing archive

    iteration = 0
    while True:
        iteration = iteration + 1  # iteration count
        # saving archive 30 seconds before closing
        for arc in archive:
            logger.info("***ARCHIVE***")
            logger.info("\nValues: " + str(
                arc.get_candidate_values()) + "\nwith objective values: " + str(
                arc.get_objective_values()) + "\nSatisfying Objective: " + str(
                arc.get_covered_objectives()))
        print("Iteration count: " + str(iteration))

        R_T = []
        Q_T = generate_off_spring(P_T, objective_uncovered,
                                  lb,ub)  # generating off spring uning ONE point crossover and uniform mutation
        evaulate_population(func, Q_T)  # evaluating offspring
        update_archive(Q_T, objective_uncovered, archive, no_of_Objectives, threshold_criteria)  # updating archive

        R_T = copy.deepcopy(P_T)  # R_T = P_T union Q_T
        R_T.extend(Q_T)

        F = preference_sort(R_T, size, objective_uncovered)  # Reference sorts and getting fronts

        if len(objective_uncovered) == 0:  # checking if all objectives are covered
            print("all_objectives_covered")
            logger.info("***Final-ARCHIVE***")
            print(("***Final-ARCHIVE***"))
            for arc in archive:
                print("\nValues: " + str(
                    arc.get_candidate_values()) + "\nwith objective values: " + str(
                    arc.get_objective_values()) + "\nSatisfying Objective: " + str(
                    arc.get_covered_objectives()))

                logger.info("\nValues: " + str(
                    arc.get_candidate_values()) + "\nwith objective values: " + str(
                    arc.get_objective_values()) + "\nSatisfying Objective: " + str(
                    arc.get_covered_objectives()))
            break

        P_T_1 = []  # creating next generatint PT+1
        index = 0

        while len(P_T_1) <= size:  # if length of current generation is less that size of front at top then add it

            if not isinstance(F[index], Candidate):
                if len(P_T_1) + len(F[index]) > size:
                    break
            else:
                if len(P_T_1) + 1 > size:
                    break

            front = F[index]
            if isinstance(F[index], Candidate):  # if front contains only one item
                P_T_1.append(F[index])
                F.remove(F[index])
            else:
                for ind in range(len(F[index])):  # if front have multiple items
                    val = F[index][ind]
                    P_T_1.append(val)

                F.remove(F[index])
        while (len(P_T_1)) < size:  # crowding distance
            copyFront = copy.deepcopy(F[index])
            sorted_front = sort_worse(copyFront)  # sort before crowding distance

            crowding_distance = get_array_for_crowding_distance(sorted_front)  # coverting to libaray compaitble array
            assign_crowding_distance_to_each_value(sorted_front,
                                                   crowding_distance)  # assinging each solution its crowding distance
            sorted_front.sort(key=sort_based_on_crowding_distance, reverse=True)  # sorting based on crowding distance

            if (len(sorted_front) + len(
                    P_T_1)) > size:  # maintaining length and adding solutions with most crowding distances
                for sorted_front_indx in range(len(sorted_front)):
                    candidate = sorted_front[sorted_front_indx]
                    P_T_1.append(candidate)
                    if len(P_T_1) >= size:
                        break

            index = index + 1

        P_T_1 = P_T_1[0:size]
        P_T = P_T_1  # assigning PT+1 to PT


def minimize(func, size, lb, ub, no_of_Objectives, criteria,time_budget,logger,archive):
    assert hasattr(func, '__call__')

    start = time.time()
    run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger,start,time_budget)



