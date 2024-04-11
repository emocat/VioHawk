import multiprocessing
import sys
sys.path.append('lib/')
import config as cfg
import time
from pymoo.factory import get_crossover, get_mutation, get_sampling
from pymoo.algorithms.so_genetic_algorithm import GA
from pymoo.optimize import minimize
from RBF import Model
from pymoo.model.problem import Problem
import pandas as pd
from utils import *

class Pylot_caseStudy(Problem):

    def __init__(self,  n_var_in=16, xl_in=0, xu_in=1, number_of_neurons=10, cluste=[],
                 ):
        super().__init__(n_var=n_var_in, n_obj=1, xl=xl_in, xu=xu_in, type_var=int, elementwise_evaluation=True)
        self.model = Model(number_of_neurons, cluste)

    def _evaluate(self, x, out, *args, **kwargs):
        if x[0] != 3:
            x[15] = 0
        value = self.model.predict(x)
        out["F"] = value


def run( objective, no_of_neurons, seed, cluster, cluster_id):
    tic = time.time()


    vals = pd.read_csv(cfg.clean_data, header=None).iloc[:, 0:16].values
    lb, ub = find_bounds(vals)
    cs = Pylot_caseStudy(n_var_in=16, xl_in=lb, xu_in=ub, number_of_neurons=no_of_neurons,
                          cluste=cluster,)
    algorithm = GA(
        pop_size=6,
        sampling=get_sampling("int_random"),
        crossover=get_crossover("int_sbx"),
        mutation=get_mutation("int_pm"),
        eliminate_duplicates=True)
    res = minimize(cs,
                   algorithm,
                   seed=seed,
                   termination=('n_gen', 200),
                   verbose=False)
    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))

    toc = time.time()
    X = res.X
    if X[0] != 3:
        X[15] = 0

    final_result = 'output/temp/RBF_HDBScan_objective_' + str(objective) + '_NoN_' + str(
        no_of_neurons) + '_cluster_' + str(cluster_id) + '.log'
    file = open(final_result, 'a')
    file.write("Best solution found:" + str(X) + "," + str(res.F) + " # Time taken: " + str(toc - tic) + "\n")


if __name__ == "__main__":
    times_of_repetitions = 1
    seed = 20
    percentage = 20
    no_of_neurons = 10
    objective = 0
    i = 0
    for objective in range(6):
            for i in range(times_of_repetitions):
                seed = seed + 1
                clusters, max_id = generate_clusters(cfg.all_data, cfg.clean_data, percentage, objective + 16)
                cluster_id = 0
                if max_id == -1:
                    cluster_id = -2
                print(max_id)
                for cluster in clusters:
                    seed = seed + 1
                    cluster_id = cluster_id + 1
                    lb, ub = find_bounds(cluster)
                    manager = multiprocessing.Manager()
                    p = multiprocessing.Process(target=run, name="run",
                                                args=( objective, no_of_neurons, seed, cluster, cluster_id,))
                    p.start()
                    p.join()
