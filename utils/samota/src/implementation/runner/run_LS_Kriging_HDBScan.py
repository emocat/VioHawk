import multiprocessing
import sys
sys.path.append('lib/')
import config as cfg
import time
from pymoo.factory import get_crossover, get_mutation, get_sampling
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
from pymoo.algorithms.so_genetic_algorithm import GA
from pymoo.optimize import minimize
from pymoo.model.problem import Problem
from utils import *

class Pylot_caseStudy(Problem):

    def __init__(self, i, n_var_in=16, xl_in=0, xu_in=1, cluste=[]):
        super().__init__(n_var=n_var_in, n_obj=1, xl=xl_in, xu=xu_in, type_var=int, elementwise_evaluation=True)

        # prepare X and Y
        X = []
        Y = []
        for d in cluste:
            X.append(d[:16])
            Y.append(d[16])     #fitness value at 15th Index
        kernel = 1.0 * RBF(1.0)  # squared-exponential kernel
        self.gpr = GaussianProcessRegressor(kernel=kernel).fit(X, Y)

    def _evaluate(self, x, out, *args, **kwargs):
        if x[0] != 3:
            x[15] = 0
        value =self.gpr.predict(x.reshape(1, -1))
        out["F"] = value

def run(i,objective,lb,ub,cluster_id,cluster,seed):
    tic = time.time()

    cs = Pylot_caseStudy(i, n_var_in=16, xl_in=lb, xu_in=ub,   cluste=cluster)
    #genetic algorithm for local search
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
    final_result = 'output/temp/KG_HDBScan_objective_' + str(objective)+"_Cluster_ID_"+str(cluster_id)  + '.log'
    file = open(final_result, 'a')
    file.write("Best solution found:" + str(X) + "," + str(res.F) + " # Time taken: " + str(toc - tic) + "\n")


if __name__ == "__main__":
    times_of_repetitions = 1
    seed = 20
    percent = 20
    objective = 0
for objective in range(6):
    for i in range(times_of_repetitions):
        seed = seed + 1
        manager = multiprocessing.Manager()
        clusters, max_id = generate_clusters(cfg.all_data, cfg.clean_data, percent, objective + 16)
        cluster_id = 0
        if max_id == -1:
            cluster_id = -2
        for cluster in clusters:
            seed = seed + 1
            cluster_id = cluster_id + 1
            lb, ub = find_bounds(cluster)
            manager = multiprocessing.Manager()
            p = multiprocessing.Process(target=run, name="run",
                                        args=(i, objective, lb, ub, cluster_id, cluster, seed))
            p.start()
            p.join()
