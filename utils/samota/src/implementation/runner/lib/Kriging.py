# -*- coding: utf-8 -*-

import numpy
import numpy as np
from sklearn import preprocessing
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF


class Kriging:

    def __init__(self, cluster = None):
            self.create_model_from_cluster(cluster)
    def create_model_from_cluster(self,cluster):
        self.scaler = preprocessing.StandardScaler()
        cluster = np.array(cluster)
        X = cluster[:, 0:16] # features from 0 to 15th index
        y = cluster[:, 16:17] # value at 16th index

        y[y < 0] = 0
        y[y > 1] = 1

        X = self.scaler.fit_transform(X)
        kernel = 1.0 * RBF(1.0)  # squared-exponential kernel
        self.model = GaussianProcessRegressor(kernel=kernel, random_state=0).fit(X, y)


    def test(self, cluster):
        mae = 0
        for i in range(len(cluster)):
            y_act = cluster[i][16]
            Y_pred = self.predict(cluster[i][:16])

            if y_act > 1:
                y_act =1
            if y_act < 0:
                y_act =0
            mae = mae + abs(y_act - Y_pred)
        self.mae = mae/len(cluster)
    
    def predict(self, value):
        value = numpy.array([value])
        B = np.reshape(value, (1, 16))
        B= (self.scaler.transform(B))
        y_pred = self.model.predict(value)
        if y_pred[0][0] > 1:
            return 1
        if y_pred[0][0] < 0:
            return 0

        return  y_pred[0][0]


