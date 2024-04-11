# -*- coding: utf-8 -*-
"""
"""

import numpy
import numpy as np
import pandas as pd
from sklearn import preprocessing


class Polynomial_Regression:

    def __init__(self, degree=-1, index =-1,filename='',cluster = None):
        if cluster == None:
            self.train(degree,index,filename)
        else:
            self.create_model_from_cluster(cluster,degree)


    def create_model_from_cluster(self,cluster,deg):
        self.scaler = preprocessing.StandardScaler()
        cluster = np.array(cluster)

        X = cluster[:, 0:16] # features from 0 to 15th index
        y = cluster[:, 16:17] # value at 16th index
        y[y < 0] = 0
        y[y > 1] = 1

        X = self.scaler.fit_transform(X)
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures
        self.poly_reg = PolynomialFeatures(degree=deg)
        X_poly = self.poly_reg.fit_transform(X)
        self.pol_reg = LinearRegression()
        self.pol_reg.fit(X_poly, y)

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

    def train(self, deg,index,filename):
        self.scaler = preprocessing.StandardScaler()
        dataset = pd.read_csv(filename)
        X = dataset.iloc[:, 0:16].values
        y = dataset.iloc[:, index:index+1].values
        X = self.scaler.fit_transform(X)
        y[y < 0] = 0
        y[y > 1] = 1
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures
        self.poly_reg = PolynomialFeatures(degree=deg)
        X_poly = self.poly_reg.fit_transform(X)
        self.pol_reg = LinearRegression()
        self.pol_reg.fit(X_poly, y)
    def predict(self, value):
        value = numpy.array([value])
        B = np.reshape(value, (1, 16))
        B= self.scaler.transform(B)

        y_pred = self.pol_reg.predict(self.poly_reg.fit_transform(B))
        if y_pred[0][0] > 1:
            return 1
        if y_pred[0][0] < 0:
            return 0
        return y_pred[0][0]


