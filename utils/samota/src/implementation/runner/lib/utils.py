import copy

from candidate import Candidate
import numpy as np
import pandas as pd
import random
import sys
from sklearn import preprocessing
import hdbscan
from sklearn.metrics import jaccard_score

scaler = preprocessing.StandardScaler()


def calculate_minimum_distance(candidate, random_pop):
    distance = 1000
    for each_candidate in random_pop:
        vals = each_candidate.get_candidate_values()
        candidate_vals = candidate.get_candidate_values()
        dist = np.linalg.norm(np.array(vals) - np.array(candidate_vals))
        if dist < distance:
            distance = dist
    return distance


def generate_adaptive_random_population(size, lb, ub, i =0):
    random_pop = []

    random_pop.append(generate_random_population(1, lb, ub)[0])

    while len(random_pop) < size:
        D = 0
        selected_candidate = None
        rp = generate_random_population(size, lb, ub)
        for each_candidate in rp:
            min_dis = calculate_minimum_distance(each_candidate, random_pop)
            if min_dis > D:
                D = min_dis
                selected_candidate = each_candidate
        random_pop.append(selected_candidate)

    return random_pop


# random value generator
def generate_random_population(size, lb, ub):
    random_pop = []

    for i in range(size):
        candidate_vals = []
        for index in range(len(lb)):
            candidate_vals.append(int(random.uniform(lb[index], ub[index])))

        random_pop.append(Candidate(candidate_vals))
    return random_pop


# dominates method, same from paper
def dominates(value_from_pop, value_from_archive, objective_uncovered):
    dominates_f1 = False
    dominates_f2 = False
    for each_objective in objective_uncovered:
        f1 = value_from_pop[each_objective]
        f2 = value_from_archive[each_objective]
        if f1 < f2:
            dominates_f1 = True
        if f2 < f1:
            dominates_f2 = True
        if dominates_f1 and dominates_f2:
            break
    if dominates_f1 == dominates_f2:
        return False
    elif dominates_f1:
        return True
    return False



def evaulate_population_using_ensemble(M_gs, pop):
    for candidate in pop:
        result = [1,1,1,1,1,1]
        uncertaininty = [0, 0, 0, 0, 0, 0]
        for M_g in M_gs:
            res,unc = M_g.predict(candidate.get_candidate_values())
            result[M_g.objective] = res
            uncertaininty[M_g.objective] = unc

        candidate.set_objective_values(result)
        candidate.set_uncertainity_values(uncertaininty)
# calling the fitness value function

def evaulate_population(func, pop):
    for candidate in pop:
        if isinstance(candidate, Candidate):
            result = func(candidate.get_candidate_values())
            candidate.set_objective_values(result)

def evaulate_population_with_archive(func, pop, already_executed):
    to_ret = []
    print("pop")
    print(pop)
    print(pop[0])
    for candidate in pop:
        if isinstance(candidate, Candidate):
            if candidate.get_candidate_values() in already_executed:
                continue

            result = func(candidate.get_candidate_values())
            candidate.set_objective_values(result)
            already_executed.append(candidate.get_candidate_values())
            to_ret.append(candidate)
    return to_ret

def exists_in_archive(archive, index):
    for candidate in archive:
        if candidate.exists_in_satisfied(index):
            return True
    return False


# searching archive
def get_from_archive(obj_index, archive):
    for candIndx in range(len(archive)):
        candidate = archive[candIndx]
        if candidate.exists_in_satisfied(obj_index):
            return candidate, candIndx
    return None


# updating archive with adding the number of objective it satisfies [1,2,3,4,[ob1,ob2, objective index]]
def update_archive(pop, objective_uncovered, archive, no_of_Objectives, threshold_criteria):
    for objective_index in range(no_of_Objectives):
        for pop_index in range(len(pop)):
            objective_values = pop[pop_index].get_objective_values()
            if objective_values[objective_index] <= threshold_criteria[objective_index]:
                if exists_in_archive(archive, objective_index):
                    archive_value, cand_indx = get_from_archive(objective_index, archive)
                    obj_archive_values = archive_value.get_objective_values()
                    if obj_archive_values[objective_index] > objective_values[objective_index]:
                        value_to_add = pop[pop_index]
                        value_to_add.add_objectives_covered(objective_index)
                        # archive.append(value_to_add)
                        archive[cand_indx] = value_to_add
                        if objective_index in objective_uncovered:
                            objective_uncovered.remove(objective_index)
                        # archive.remove(archive_value)
                else:
                    value_to_add = pop[pop_index]
                    value_to_add.add_objectives_covered(objective_index)
                    archive.append(value_to_add)
                    if objective_index in objective_uncovered:
                        objective_uncovered.remove(objective_index)


# method to get the most dominating one
def select_best(tournament_candidates, objective_uncovered):
    best = tournament_candidates[0]  # in case none is dominating other
    for i in range(len(tournament_candidates)):
        candidate1 = tournament_candidates[i]
        for j in range(len(tournament_candidates)):
            candidate2 = tournament_candidates[j]
            if (dominates(candidate1.get_objective_values(), candidate2.get_objective_values(), objective_uncovered)):
                best = candidate1
    return best


def tournament_selection_improved(pop, size, objective_uncovered):
    tournament_candidates = []
    for i in range(size):
        indx = random.randint(0, len(pop) - 1)
        random_candidate = pop[indx]
        tournament_candidates.append(random_candidate)

    best = select_best(tournament_candidates, objective_uncovered)
    return best;


def tournament_selection(pop, size, objective_uncovered):
    tournament_candidates = []
    for i in range(size):
        indx = random.randint(0, len(pop) - 1)
        random_candidate = pop[indx]
        tournament_candidates.append(random_candidate)

    best = select_best(tournament_candidates, objective_uncovered)
    return best;


def do_single_point_crossover(parent1, parent2):  
    parent1 = parent1.get_candidate_values();
    parent2 = parent2.get_candidate_values()
    crossover_point = random.randint(1, len(parent1) - 1)
    t_parent1 = parent1[0:crossover_point]
    t_parent2 = parent2[0:crossover_point]
    for i in range(crossover_point, len(parent1)):
        t_parent1.append(parent2[i])
        t_parent2.append(parent1[i])

    return Candidate(t_parent1), Candidate(t_parent2)


def do_uniform_mutation(parent1, parent2, lb, ub, threshold):
    child1 = []
    child2 = []

    parent1 = parent1.get_candidate_values();
    parent2 = parent2.get_candidate_values()

    for parent1_index in range(len(parent1)):
        probability_mutation = random.uniform(0, 1)
        if probability_mutation <= threshold:
            random_value = random.uniform(lb[parent1_index], ub[parent1_index])
            child1.append(int(random_value))
        else:
            child1.append(parent1[parent1_index])

    for parent2_index in range(len(parent2)):
        probability_mutation = random.uniform(0, 1)
        if probability_mutation <=threshold:  # 1/4         25% probability
            random_value = random.uniform(lb[parent2_index], ub[parent2_index])
            child2.append(int(random_value))
        else:
            child2.append(parent2[parent2_index])

    return Candidate(child1), Candidate(child2)


def generate_off_spring(pop, objective_uncovered, lb,ub):
    size = len(pop)
    population_to_return = []
    while (len(population_to_return) < size):
        parent1 = tournament_selection(pop, 10, objective_uncovered)  # tournament selection same size as paper
        parent2 = tournament_selection(pop, 10, objective_uncovered)
        probability_crossover = random.uniform(0, 1)
        if probability_crossover <= 0.75:  # 75% probability
            parent1, parent2 = do_single_point_crossover(parent1, parent2)  
        child1, child2 = do_uniform_mutation(parent1, parent2, lb, ub, (1 / len(parent1.get_candidate_values())))
        population_to_return.append(child1)
        population_to_return.append(child2)
    return population_to_return




def correct(Q_T, lb, ub):
    for indx in range(len(Q_T)):
        candidate = Q_T[indx]
        values = candidate.get_candidate_values();
        for value_index in range(len(values)):
            Q_T[indx].set_candidate_values_at_index(value_index, int(Q_T[indx].get_candidate_values()[value_index]))
            if values[value_index] > ub[value_index] or values[value_index] < lb[value_index]:
                temp = generate_random_population(1, lb, ub)[0];
                Q_T[indx].set_candidate_values_at_index(value_index, int(temp.get_candidate_values()[value_index]))

    return Q_T


def do_simulated_binary_crossover(parent1, parent2, nc=20):
    parent1 = parent1.get_candidate_values();
    parent2 = parent2.get_candidate_values()
    u = random.uniform(0, 1)
    # half Raja's code, as the child candidates was too close
    if u < 0.5:
        B = (2 * u) ** (1 / (nc + 1))
    else:
        B = (1 / (2 * (1 - u))) ** (1 / (nc + 1))
    t_parent1 = []
    t_parent2 = []

    for indx in range(len(parent1)):
        x1 = parent1[indx]
        x2 = parent2[indx]
        x1new = 0.5 * (((1 + B) * x1) + ((1 - B) * x2))
        x2new = 0.5 * (((1 - B) * x1) + ((1 + B) * x2))
        t_parent1.append(x1new)
        t_parent2.append(x2new)

    return Candidate(t_parent1), Candidate(t_parent2)


def do_gaussain_mutation_for_one(parent1_cand, lb, ub, thresh):
    parent1 = parent1_cand.get_candidate_values()

    for attrib in range(len(parent1)):
        if random.uniform(0, 1) > thresh:
            continue
        mu = 0;
        sigma = 1
        alpha = np.random.normal(mu, sigma)
        actualValueP1 = parent1[attrib];

        if (alpha < 1) and (alpha >= 0):
            if actualValueP1 + 1 < ub[attrib]:
                parent1[attrib] = parent1[attrib] + 1;
        elif (alpha <= 0) and (alpha > -1):
            if actualValueP1 - 1 > lb[attrib]:
                parent1[attrib] = parent1[attrib] - 1;
        else:
            if actualValueP1 + alpha < ub[attrib]:
                parent1[attrib] = parent1[attrib] + alpha;
    return Candidate(parent1)


def do_gaussain_mutation(parent1_cand, parent2_cand, lb, ub, thresh):
    parent1 = parent1_cand.get_candidate_values()
    parent2 = parent2_cand.get_candidate_values()
    for attrib in range(len(parent1)):
        random_value_for_theshold = random.uniform(0, 1);
        if random_value_for_theshold > thresh:
            continue
        mu = 0;
        sigma = 1

        alpha = np.random.normal(mu, sigma)
        actualValueP1 = parent1[attrib];
        actualValueP2 = parent2[attrib];

        if (alpha < 1) and (alpha >= 0):
            if actualValueP1 + 1 < ub[attrib]:
                parent1[attrib] = parent1[attrib] + 1;
            if actualValueP2 + 1 < ub[attrib]:
                parent2[attrib] = parent2[attrib] + 1;

        elif (alpha <= 0) and (alpha > -1):
            if actualValueP1 - 1 > lb[attrib]:
                parent1[attrib] = parent1[attrib] - 1;
            if actualValueP2 - 1 > lb[attrib]:
                parent2[attrib] = parent2[attrib] - 1;
        else:
            if actualValueP1 + alpha < ub[attrib]:
                parent1[attrib] = parent1[attrib] + alpha;
            if actualValueP2 + alpha < ub[attrib]:
                parent2[attrib] = parent2[attrib] + alpha;

    return Candidate(parent1), Candidate(parent2)


def get_distribution_index(parent1, parent2, objective_uncovered, threshold_criteria):
    total = 0;
    for each_obj in objective_uncovered:
        total = total + parent1.get_objective_value(each_obj) - 0.95
        total = total + parent2.get_objective_value(each_obj) - 0.95

    total = total / (len(objective_uncovered) * 2)

    return 21 - (total * 400)


def recombine_improved(pop, objective_uncovered, lb, ub, threshold_criteria):
    size = len(objective_uncovered)

    population_to_return = []

    if size == 1:
        candidate = do_gaussain_mutation_for_one(pop[0], lb, ub, (1 / len(pop[0].get_candidate_values())))
        population_to_return.append(candidate)

    else:
        while len(population_to_return) < size:
            parent1 = tournament_selection_improved(pop, 2,
                                                    objective_uncovered)  # tournament selection same size as paper
            parent2 = tournament_selection_improved(pop, 2, objective_uncovered)
            while parent1 == parent2:
                parent2 = tournament_selection_improved(pop, 2, objective_uncovered)
            probability_crossover = random.uniform(0, 1)
            if probability_crossover <= 0.60:  # 60% probability
                print("getting distribution index")
                nc = get_distribution_index(parent1, parent2, objective_uncovered, threshold_criteria);
                parent1, parent2 = do_simulated_binary_crossover(parent1, parent2, nc)  
            child1, child2 = do_gaussain_mutation(parent1, parent2, lb, ub, (1 / len(parent1.get_candidate_values())))

            population_to_return.append(child1)
            population_to_return.append(child2)

    return population_to_return
    # 0 Road type [categorical]
    # 1 Road ID [categorical]
    # 2 Scenario Length [categorical]
    # 3 Vehicle_in_front [categorical]
    # 4 vehicle_in_adjcent_lane [categorical]
    # 5 vehicle_in_opposite_lane [categorical]
    # 6 vehicle_in_front_two_wheeled [categorical]
    # 7 vehicle_in_adjacent_two_wheeled [categorical]
    # 8 vehicle_in_opposite_two_wheeled [categorical]
    # 9 time of day [ordinal]
    # 10 weather [ordinal]
    # 11 Number of People [categorical]
    # 12 Target Speed [numeric]
    # 13 Trees in scenario [categorical]
    # 14 Buildings in Scenario [categorical]
    # 15 task [categorical]

def calculate_distance(list_x, list_y, types=None):

    # to easily manage types (and possible values) for individual attributes
    if not types:
        types = [
            ('nominal', None),  # 0 road type
            ('nominal', None),  # 1 road ID
            ('nominal', None),  # 2 scenario length
            ('nominal', None),  # 3 Vehicle_in_front [categorical]
            ('nominal', None),  # 4 vehicle_in_adjcent_lane [categorical]
            ('nominal', None),  # 5 vehicle_in_opposite_lane [categorical]
            ('nominal', None),  # 6 vehicle_in_front_two_wheeled [categorical]
            ('nominal', None),  # 7 vehicle_in_adjacent_two_wheeled [categorical]
            ('nominal', None),  # 8  vehicle_in_opposite_two_wheeled [categorical]
            ('ordinal', 2),     # 9 time of day [ordinal]
            ('ordinal', 6),     # 10 weather [ordinal]
            ('nominal', None),  # 11 Number of People [categorical]
            ('numeric', 4),     # 12 Target Speed [numeric]
            ('nominal', None),  # 13 Trees in scenario [categorical]
            ('nominal', None),  # 14 Buildings in Scenario [categorical]
            ('nominal', None),  # 15 task [categorical]
            # NOTE: for an ordinal attribute having n possible values, a value in a vector must be one of {1, 2, ..., n}
            # FIXME: complete this list
        ]
    assert len(list_x) == len(list_y)
    # assert len(types) == len(list_x)

    distance_sum = 0
    for i in range(len(types)):
        attr_dist = 0  # the distance for each attribute; normalized between 0 and 1
        if types[i][0] == 'nominal':
            # distance calculation for a nominal attribute
            if list_x[i] == list_y[i]:
                attr_dist = 0
            else:
                attr_dist = 1
        elif types[i][0] == 'ordinal':
            # distance calculation for an ordinal attribute
            max_rank = types[i][1]
            z_x = (list_x[i]) / (max_rank)
            z_y = (list_y[i]) / (max_rank)
            attr_dist = abs(z_x - z_y)
        elif types[i][0] == 'numeric':
            # distance calculation for a numeric attribute
            max_value = types[i][1]
            attr_dist = abs(list_x[i] - list_y[i]) / max_value
        else:
            print(f'Error - Unknown type: {types[i][0]} in calculate_distance()')
            exit(-1)
        distance_sum += attr_dist
    distance = distance_sum / len(list_x)
    return distance

# def calculate_distance(list_x, list_y):
#     distance = 0
#     for i in range(len(list_x)):
#         if 0 <= i < 9:
#             if list_x[i] != list_y[i]:
#                     distance = distance+1
#         elif 9 <= i < 11:
#             if i == 9:
#                 d1 = list_x[i]/2
#                 d2 = list_y[i]/2
#                 distance = distance + abs(d1-d2)
#             if i == 10:
#                 d1 = list_x[i]/6
#                 d2 = list_y[i]/6
#                 distance = distance + abs(d1-d2)
#         elif i == 11:
#             if list_x[i] != list_y[i]:
#                     distance = distance+1
#         elif i == 12:
#             d1 = list_x[i]-2 / 2
#             d2 = list_y[i]-2 / 2
#             distance = distance + abs(d1 - d2)
#         else:
#             if list_x[i] != list_y[i]:
#                 distance = distance + 1
#     return distance

def get_top_five_according_jaccard_distance(value, temp_X):

    all_feature_vectors_with_distances = []
    for val in temp_X:
        distance = calculate_distance(val,value)
        feature_vector_with_distance = copy.deepcopy(val)
        feature_vector_with_distance.append(distance)
        all_feature_vectors_with_distances.append(feature_vector_with_distance)
    sorted_data = sorted(all_feature_vectors_with_distances, key=lambda x: x[17])
    return sorted_data[0:5]



def generate_one_cluster(file_name, clean_data, percent, index):
    pre_process_data(file_name, percent, index, clean_data)
    dataset = pd.read_csv(clean_data,header=None)
    X = dataset.iloc[:, 0:16].values.tolist()
    Y = dataset.iloc[:, index:index + 1].values.tolist()

    for index in range(len(X)):
        if (Y[index][0]<0):
            X[index].append(0)
        else:
            X[index].append(Y[index][0])

    # sys.exit(0)
    return X, 1

def generate_clusters_one_for_top_n(file_name, clean_data, percent, index):
    pre_process_data(file_name, percent, index, clean_data)
    dataset = pd.read_csv(clean_data,header=None)
    X = dataset.iloc[:, 0:16].values.tolist()
    Y = dataset.iloc[:, index:index + 1].values.tolist()
    for index in range(len(X)):
        X[index].append(Y[index][0])

    # sys.exit(0)
    cluster = []
    for value in X:
        temp_X = copy.deepcopy(X)
        temp_X.remove(value)
        top_five = get_top_five_according_jaccard_distance(value, temp_X)
        top_five = [x[0:17] for x in top_five]
        cluster.append(top_five)
    return cluster, len(cluster)

def train_test_spilt(cluster, train_percentage):
    random.shuffle(cluster)
    train = []
    test = []
    test_percentage = 100 - train_percentage
    for i in range(int(((len(cluster) * train_percentage) / 100))):
        train.append(cluster[i])

    total = 0
    for i in range(int(((len(cluster) * train_percentage) / 100)),
                   int(((len(cluster) * train_percentage) / 100)) + 1 + int(((len(cluster) * test_percentage) / 100))):

        if i <len(cluster):
            test.append(cluster[i])
    return train, test


def create_database(all_data,clean_data):
    database = []
    pre_process_data(all_data, 100, 16, clean_data)

    dataset = pd.read_csv(clean_data, header=None)
    X = dataset.iloc[:, 0:16].values
    Y = dataset.iloc[:, 16:].values
    Y[Y<0] =0 #rounding violation
    for i in range(len(X)):
        cd = Candidate(X[i].tolist())
        cd.set_objective_values(Y[i].tolist())
        database.append(cd)
    return database

def preprocess_data(database2,percent,index):
    all_combined = []
    database = copy.deepcopy(database2)
    for c in database:
        to_add = c.get_candidate_values()
        to_add.extend(c.get_objective_values())
        all_combined.append(to_add)

    sorted_data = sorted(all_combined, key=lambda x: x[index])
    file_writer = open("clean_data.csv", 'w')
    to_write_count =(int((len(all_combined) * percent) / 100))
    if to_write_count<5:
        to_write_count =5
    for i in range(to_write_count):
        if i >= len(sorted_data):
            break
        to_write = str(sorted_data[i]).replace('[', '').replace(']', '') + "\n"
        file_writer.write(to_write)

def generate_clusters_using_database(database,percent,index):
    index = index + 16
    preprocess_data(database,percent,index)
    dataset = pd.read_csv("clean_data.csv",header=None)
    X = dataset.iloc[:, 0:16].values
    Y = dataset.iloc[:, index:index + 1].values
    X = scaler.fit_transform(X)
    clusterer = hdbscan.HDBSCAN(algorithm='best', metric=calculate_distance)
    clusterer.fit(X)
    all_data_clusters = []
    for label in range(0, clusterer.labels_.max() + 1):
        array = values_with_label(X, label, clusterer.labels_, Y)
        all_data_clusters.append(array)
    if clusterer.labels_.max() == -1:
        array = values_with_label(X, -1, clusterer.labels_, Y)
        all_data_clusters.append(array)
        return all_data_clusters, -1

    return all_data_clusters,clusterer.labels_.max()

def generate_clusters(file_name, clean_data, percent, index):
    pre_process_data(file_name, percent, index, clean_data)
    dataset = pd.read_csv(clean_data,header=None)
    X = dataset.iloc[:, 0:16].values
    Y = dataset.iloc[:, index:index + 1].values
    X = scaler.fit_transform(X)
    clusterer = hdbscan.HDBSCAN(algorithm='best', metric=calculate_distance)
    clusterer.fit(X)
    all_data_clusters = []
    for label in range(0, clusterer.labels_.max() + 1):
        array = values_with_label(X, label, clusterer.labels_, Y)
        all_data_clusters.append(array)
    if clusterer.labels_.max() == -1:
        array = values_with_label(X, -1, clusterer.labels_, Y)
        all_data_clusters.append(array)
        return all_data_clusters, -1

    return all_data_clusters,clusterer.labels_.max()


def values_with_label(X, label, labels, values):
    to_ret = []
    for val in range(len(labels)):
        # if labels[val] == label:
        #     arr = X[val]
        #     arr = scaler.inverse_transform(arr)
        #     arr = [int(x) for x in arr]
        #     if values[val] < 0:
        #         arr = np.append(arr,0)
        #     else:
        #         arr = np.append(arr, values[val])

        #     to_ret.append(arr)
        ############ 一维转化为二维
        if labels[val] == label:
            arr = X[val].reshape(1, -1)  
            arr = scaler.inverse_transform(arr)
            arr = arr.astype(int)  
            if values[val] < 0:
                arr = np.append(arr, 0)
            else:
                arr = np.append(arr, values[val])

            to_ret.append(arr.flatten())  
    return to_ret


def find_bounds(cluster):
    # print(cluster)
    ub = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0]
    lb = [3, 3, 0, 1, 1, 1, 1, 1, 1, 2, 6, 1, 4, 1, 1, 2]

    for feature_vector in cluster:
        fv = feature_vector[0:16]

        for i in range(len(fv)):
            if fv[i] < lb[i]:
                lb[i] = fv[i]
            if fv[i] > ub[i]:
                ub[i] = fv[i]
    return lb, ub


def pre_process_data(file_name, percent, index, filename):
    file_reader = open(file_name, 'r')
    all_data = file_reader.read()
    data_parts = all_data.split("\n")
    total_parts = len(data_parts)
    all_data_float = []
    for data in data_parts:
        if len(data) > 0:
            data_part = data.split(" [")
            data_part = data_part[1].replace("]:", ",")
            dp = list(data_part.split(","))
            dp = [float(ind) for ind in dp]
            all_data_float.append(dp)
    sorted_data = sorted(all_data_float, key=lambda x: x[index])
    file_writer = open(filename, 'w')

    for i in range(int((total_parts * percent) / 100)):
        if i>= len(sorted_data):
            break
        to_write = str(sorted_data[i]).replace('[', '').replace(']', '') + "\n"
        file_writer.write(to_write)


def recombine(pop, objective_uncovered, lb, ub):
    size = len(pop)

    population_to_return = []
    if size == 1:
        candidate = do_gaussain_mutation_for_one(pop[0], lb, ub, (1 / len(pop[0].get_candidate_values())))
        population_to_return.append(candidate)          
    else:
        while len(population_to_return) < size:
            parent1 = tournament_selection(pop, 2, objective_uncovered)  # tournament selection same size as paper
            parent2 = tournament_selection(pop, 2, objective_uncovered)
            while parent1 == parent2:
                parent2 = tournament_selection(pop, 2, objective_uncovered)
            probability_crossover = random.uniform(0, 1)
            if probability_crossover <= 0.60:  # 60% probability
                parent1, parent2 = do_simulated_binary_crossover(parent1, parent2)  
            child1, child2 = do_gaussain_mutation(parent1, parent2, lb, ub, (1 / len(parent1.get_candidate_values())))

            population_to_return.append(child1)
            if len(population_to_return) < size:
                population_to_return.append(child2)

    return population_to_return


