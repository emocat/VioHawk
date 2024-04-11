import copy

from utils import *


def  environment_selection(objective_uncovered, R_T):
    to_return = []
    for obj in objective_uncovered:
        min = 10000
        selected_candidate = None
        for candidate in R_T:
            if candidate.get_objective_value(obj) < min:
                min = candidate.get_objective_value(obj)
                selected_candidate = candidate
        if selected_candidate not in to_return:
            if selected_candidate is not None:
                to_return.append(selected_candidate)
           
    return to_return


def run_search(func, size, lb, ub, no_of_Objectives, criteria, archive,logger):
    threshold_criteria = criteria
    objective_uncovered = []

    for obj in range(no_of_Objectives):
        objective_uncovered.append(obj)  # initialising number of uncovered objective

    random_population = generate_adaptive_random_population(size, lb, ub)  # Generating random population

    P_T = copy.copy(random_population)

    evaulate_population(func, random_population)  # evaluating whole generation and storing results

    update_archive(random_population, objective_uncovered, archive, no_of_Objectives,
                   threshold_criteria)  # updateing archive

    iteration = 0
    while True:
        iteration = iteration + 1  # iteration count
        print("Iteration count: " + str(iteration))
        print("Objective  Uncovered")
        print(objective_uncovered)
        print("****")
#        logger.info("Uncov objs: "+str(objective_uncovered))

        R_T = []

        #print("Starting recombine")
        Q_T = recombine(P_T, objective_uncovered,
                        lb, ub)  #
        #print("Recombine")
        Q_T = correct(Q_T, lb, ub)
        #print("correct")
        #print(Q_T)

#        sys.exit(0)

        evaulate_population(func, Q_T)  # evaluating offspring
        #print("evaulate_population(func, Q_T) ")
        update_archive(Q_T, objective_uncovered, archive, no_of_Objectives, threshold_criteria)  # updating archive
        #print("Update ARchive")
        R_T = copy.deepcopy(P_T)  # R_T = P_T union Q_T
        R_T.extend(Q_T)
        if len(objective_uncovered) == 0:  # checking if all objectives are covered
            print("All Objectives Covered")
            break
        P_T_1 = environment_selection(objective_uncovered, R_T)
      #  print("Environment selections")
        P_T = P_T_1  # assigning PT+1 to PT
      #  print(len(P_T))



def minimize(func, size, lb, ub, no_of_Objectives, criteria,time_budget,logger,archive):
    assert hasattr(func, '__call__')



    run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger)
