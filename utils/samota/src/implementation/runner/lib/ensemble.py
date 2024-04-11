# -*- coding: utf-8 -*-

from  RBF import Model as RBF_Model
from PR import Polynomial_Regression
from Kriging import *
from utils.samota.src.implementation.runner.lib.utils import train_test_spilt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
import copy


class ensemble:
    def __init__(self,database,obj,deg=2):
        self.objective = obj

        train, test = train_test_spilt(database,80)
        self.rbf = RBF_Model(10, train)
        self.PR = Polynomial_Regression(degree=deg, cluster = train)
        self.KR = Kriging(train)

        self.rbf.test(test)
        self.PR.test(test)
        self.KR.test(test)



        total_mae = self.rbf.mae + self.PR.mae + self.KR.mae
        self.w_rbf = 0.5 * ((total_mae - self.rbf.mae)/total_mae)
        self.w_PR = 0.5 * ((total_mae - self.PR.mae) / total_mae)
        self.w_KR = 0.5 * ((total_mae - self.KR.mae) / total_mae)




    def predict (self,fv):
        fv = fv[:16]
        # fv = [0, 1, 0, 0, 0, 0, 1, 1, 1, 2, 3, 1, 4, 1, 1, 1]
        # print(fv)
        y_rbf = self.rbf.predict(copy.deepcopy(fv))
        y_pr = self.PR.predict(copy.deepcopy(fv))
        y_kr = self.KR.predict(copy.deepcopy(fv))


        diff_rbf_pr = abs(y_rbf - y_pr)
        diff_rbf_kr = abs(y_rbf - y_kr)
        diff_pr_kr = abs(y_pr - y_kr)

        # print(y_pr)
        # print((y_rbf*self.w_rbf) + (y_pr*self.w_PR) + (y_kr*self.w_KR))

        
        # print(diff_pr_kr,diff_rbf_kr,diff_rbf_pr)
        

        return (y_rbf*self.w_rbf) + (y_pr*self.w_PR) + (y_kr*self.w_KR), max([diff_rbf_pr,diff_rbf_kr,diff_pr_kr])
