import multiprocessing
import sys
sys.path.append('lib/')
import config as cfg
import time
from pymoo.factory import get_crossover, get_mutation, get_sampling
from pymoo.algorithms.so_genetic_algorithm import GA
from pymoo.optimize import minimize
from PR import Polynomial_Regression
from pymoo.model.problem import Problem
import pandas as pd
from utils import *

class Pylot_caseStudy(Problem):
    def __init__(self,i,n_var_in=16, xl_in=0, xu_in=1,  degree = 3, index = 16):
        super().__init__(n_var=n_var_in, n_obj=1,  xl=xl_in, xu=xu_in, type_var=int, elementwise_evaluation=True)
        self.model = Polynomial_Regression(degree, index,cfg.clean_data)
    def _evaluate(self,x, out, *args, **kwargs):
        if x[0]!= 3:
            x[15] = 0
        value = self.model.predict(x)
        out["F"] = value
def run(i,objective,deg,seed):
    tic = time.time()
    ind = objective+16
    percentage = 20
    pre_process_data(cfg.all_data, percentage, ind, cfg.clean_data)
    vals = pd.read_csv(cfg.clean_data,header=None).iloc[:, 0:16].values
    lb, ub = find_bounds(vals)
    cs = Pylot_caseStudy(i, n_var_in= 16, xl_in=lb, xu_in = ub, degree = deg,index =ind)
    algorithm = GA(
        pop_size=6,
        sampling=get_sampling("int_random"),
        crossover=get_crossover("int_sbx"),
        mutation=get_mutation("int_pm"),
        eliminate_duplicates=True)
    res = minimize(cs,
                   algorithm,
                   seed = seed,
                   termination=('n_gen', 200),
                   verbose=False)
    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))

    toc =  time.time()
    X = res.X
    if X[0] != 3:
        X[15] = 0

    final_result = 'output/temp/PR_objective_'+str(objective)+'degree_'+str(deg) + '.log'
    file = open (final_result,'a')
    file.write("Best solution found:" +str(X)+","+str (res.F)+" # Time taken: " + str(toc -tic)+"\n")

if __name__ == "__main__":
    times_of_repetitions = 1
    seed = 20
    deg = 2
    for objective in range (6):
            for i in range(times_of_repetitions):
                seed = seed + 1
                manager = multiprocessing.Manager()
                p = multiprocessing.Process(target=run, name="run", args=(i, objective,deg,seed,))
                p.start()
                p.join()
