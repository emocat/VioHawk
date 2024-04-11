import copy
import time
import sys
sys.path.append('src/implementation/runner/lib/')
import numpy
import numpy as np
from RBF import Model as RBF_Model
from candidate import Candidate
from ensemble import ensemble
from pymoo.algorithms.nsga2 import calc_crowding_distance
from pymoo.algorithms.so_genetic_algorithm import GA
from pymoo.factory import get_crossover, get_mutation, get_sampling
from pymoo.model.problem import Problem
from pymoo.optimize import minimize as min_GA
from utils.samota.src.implementation.runner.lib.utils import *


# from smt.sampling_methods import LHS

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

    if len(to_return) >= size:
        F1 = R_T
        for i in range(len(F1)):
            to_return.append(F1[i])
    else:
        E = fast_dominating_sort(R_T, objective_uncovered)
        for i in range(len(E)):
            to_return.append(E[i])
    return to_return


# converting to numpy array (Required by library)
def get_array_for_crowding_distance(sorted_front):
    list = []
    for value in sorted_front:
        objective_values = value.get_objective_values()

        np_array = numpy.array([objective_values[0], objective_values[1],objective_values[2],objective_values[3],objective_values[4],
                                objective_values[5]
                                ])
        list.append(np_array)

    np_list = np.array(list)
    cd = calc_crowding_distance(np_list)
    return cd
# method to assign each candidate its crownding distance
def assign_crowding_distance_to_each_value(sorted_front, crowding_distance):
    for candidate_index in range(len(sorted_front)):
        objective_values = sorted_front[candidate_index]
        objective_values.set_crowding_distance(crowding_distance[candidate_index])

def get_data_for_objective(database_2,index):
    to_ret  = []
    database = copy.deepcopy(database_2)
    for data in database:
        d = data.get_candidate_values()
        d.append(data.get_objective_value(index))
        to_ret.append(d)
    return to_ret


def train_globals(database,objective_uncovered):
    ensemble_models = []
    for obj in objective_uncovered:
        db = get_data_for_objective(database,obj)
        ensemble_model = ensemble(db,obj)
        ensemble_models.append(ensemble_model)
    return ensemble_models

def update_iteration_bests(R_T,iteartion_b,iteration_n,objective_uncovered):
    for objective in objective_uncovered:
        best_b = R_T[0]
        best_n = R_T[0]
        for candidate in R_T:
            if candidate.get_objective_value(objective) < best_b.get_objective_value(objective):
                best_b = candidate
            if candidate.get_uncertainity_value(objective) > best_n.get_uncertainity_value(objective):
                best_n = candidate

        if len(iteartion_b[objective])==0:
            iteartion_b[objective] = best_b
        else:
            if best_b.get_objective_value(objective) < iteartion_b[objective].get_objective_value(objective):
                iteartion_b[objective] = best_b

        if len(iteration_n[objective]) == 0:
            iteration_n[objective] = best_n
        else:
            if best_n.get_uncertainity_value(objective) > iteration_n[objective].get_uncertainity_value(objective):
                iteration_n[objective] = best_n


    return iteartion_b,iteration_n, R_T

def update_global_bests(T_b,iteration_b):
    imp = False
    for index in range(len(T_b)):
        if isinstance(T_b[index], Candidate):
            if iteration_b[index].get_objective_value(index) < T_b[index].get_objective_value(index):
                imp = True
                T_b[index] = iteration_b[index]
        else:
            if isinstance(iteration_b[index], Candidate):
                imp = True
                T_b[index]= iteration_b[index]
    return T_b,imp

def update_global_bests_uncertainity(T_b, iteration_b):
        for index in range(len(T_b)):
            if isinstance(T_b[index], Candidate):
                if iteration_b[index].get_uncertainity_value(index) > T_b[index].get_uncertainity_value(index):
                    T_b[index] = iteration_b[index]
            else:
                if isinstance(iteration_b[index], Candidate):
                    T_b[index] = iteration_b[index]
        return T_b


def GS (database,obj_uncovered,size,g_max,criteria,lb,ub):
    objective_uncovered = copy.deepcopy(obj_uncovered)
    M_g = train_globals(database,objective_uncovered)
    T_b,T_n = [[],[],[],[],[],[]],[[],[],[],[],[],[]]
    iteration = 0
    P_T = generate_random_population(size, lb, ub)  # Generating random population
    evaulate_population_using_ensemble(M_g,P_T)
    while iteration<g_max:
        iteartion_b, iteration_n = [[], [], [], [], [], []], [[], [], [], [], [], []]
        iteration = iteration + 1  # iteration count
        R_T = []
        Q_T = generate_off_spring(P_T, objective_uncovered,
                                  lb,ub)  # generating off spring uning ONE point crossover and uniform mutation
        evaulate_population_using_ensemble(M_g, Q_T)  # evaluating offspring
        # update_archive(Q_T, objective_uncovered, archive, no_of_Objectives, threshold_criteria)  # updating archive
        R_T = copy.deepcopy(P_T)  # R_T = P_T union Q_T
        R_T.extend(Q_T)
        iteartion_b,iteration_n, R_T = update_iteration_bests(R_T,iteartion_b,iteration_n,objective_uncovered)
        T_b,_ = update_global_bests(T_b,iteartion_b)

        T_n = update_global_bests_uncertainity(T_n, iteration_n)
        
        F = preference_sort(R_T, size, objective_uncovered)  # Reference sorts and getting fronts
        if len(objective_uncovered) == 0:  # checking if all objectives are covered
            print("All Objectives Covered")
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
    T_b.extend(T_n)
    return T_b




class Pylot_caseStudy(Problem):
    def __init__(self, i, n_var_in=16, xl_in=0, xu_in=1, number_of_neurons=10, index=16, percent=20, cluste=[],
                 clusters=-1):
        super().__init__(n_var=n_var_in, n_obj=1, xl=xl_in, xu=xu_in, type_var=int, elementwise_evaluation=True)
   
        self.model = RBF_Model(number_of_neurons, cluste)

    def _evaluate(self, x, out, *args, **kwargs):
        if x[0] != 3:
            x[15] = 0
        value = self.model.predict(x)
        out["F"] = value


def run(i, objective, no_of_neurons, sed, cluster, cluster_id,lb,ub):
    ind = objective + 16
    cs = Pylot_caseStudy(i, n_var_in=16, xl_in=lb, xu_in=ub, number_of_neurons=no_of_neurons, index=ind,
                         percent=20, cluste=cluster, clusters=cluster_id)
    algorithm = GA(
        pop_size=6,
        sampling=get_sampling("int_random"),
        crossover=get_crossover("int_sbx"),
        mutation=get_mutation("int_pm"),
        eliminate_duplicates=True)
    res = min_GA(cs,
                   algorithm,
                   seed=sed,
                   termination=('n_gen', 200),
                   verbose=False)
    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))
    toc = time.time()
    X = res.X
    if X[0] != 3:
        X[15] = 0
    return X,res.F[0]

def LS(database,objective_uncovered,size,l_max,criteria,lb,ub):
    seed = 0
    T_l = []
    for obj in objective_uncovered:
        clusters, cluster_id = generate_clusters_using_database(database, 20, obj)
        cluster_best_fv = None
        cluster_best_ov = 1
        for cluster in clusters:
            seed = seed + 1
            i = seed
            cluster_id = cluster_id + 1
            lb, ub = find_bounds(cluster)
            X,R = run(i, obj, 10, seed, cluster, cluster_id,lb,ub)
            # if R < cluster_best_ov:
            cluster_best_fv = X
            cluster_best_ov = R
            T_l.append(Candidate(cluster_best_fv))
    return T_l

def  remove_covered_objs(T_g):
    to_ret = []
    for g in T_g:
        if isinstance(g,Candidate):
            to_ret.append(g)
    return to_ret

def run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger,start,time_budget,database,g_max):
    print("Running SAMOTA")
    threshold_criteria = criteria
    already_executed=[]
    objective_uncovered = []
    for obj in range(no_of_Objectives):
        objective_uncovered.append(obj)  # initialising number of uncovered objective
    # random_population = generate_random_population_using_LHS(size, lb, ub)  # Generating random population
    random_population =[]

    random_population = generate_adaptive_random_population(size, lb, ub)  # Generating random population
    random_population = evaulate_population_with_archive(func, random_population,already_executed)  # evaluating whole generation and storing results

    database.extend(copy.deepcopy(random_population))
    update_archive(random_population, objective_uncovered, archive, no_of_Objectives,
                   threshold_criteria)  # updateing archive
    iteration = 0
    while(True):
        print("Iteration: "+str(iteration))
        T_g = GS (database,objective_uncovered,size,g_max,criteria,lb,ub)
        T_g = remove_covered_objs(T_g)
        T_g = evaulate_population_with_archive(func, T_g,already_executed)
        update_archive(T_g, objective_uncovered, archive, no_of_Objectives,
                       threshold_criteria)
        database.extend(T_g)

        T_l = LS(database,objective_uncovered,size,g_max,criteria,lb,ub)
        T_l = evaulate_population_with_archive(func, T_l,already_executed)

        update_archive(T_l, objective_uncovered, archive, no_of_Objectives,
                       threshold_criteria)
        database.extend(T_l)
        iteration = iteration + 1




def minimize(func, size, lb, ub, no_of_Objectives, criteria,time_budget,logger,archive,database,g_max):
    assert hasattr(func, '__call__')

    start = time.time()
    run_search(func, size, lb, ub, no_of_Objectives, criteria,archive,logger,start,time_budget,database,g_max)



