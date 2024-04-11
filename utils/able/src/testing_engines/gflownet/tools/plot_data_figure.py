import csv

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#
# x=np.arange(1,10,0.2)
# y= np.exp(x)
# plt.scatter(x,y)
# plt.rcParams.update({'figure.figsize':(10,8), 'figure.dpi':100})
# plt.title('Exponential Relation dataset')
# plt.show()

import random
import seaborn as sns

sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
sns.set_theme(style="ticks", color_codes=True)
path1 = 'plot_data/apollo6/difficulty_plot_data.csv'
data = pd.read_csv(path1)
g = sns.catplot(x="Methods", y="Difficulty Degree", hue="New", col="Session", height=3, aspect=0.9, col_wrap=4, kind="swarm", data=data)
sns.move_legend(g, "upper left", bbox_to_anchor=(.88, .80), title='New')
plt.show(block=True)


path = 'plot_data/apollo6/increase_plot_data.csv'
in_data = pd.read_csv(path)
g = sns.relplot(data=in_data, x="#Testing Scenarios", y="#Violation Formulae", hue="Methods", col="Session",
                height=3, aspect=0.9, col_wrap=4, kind='line')
sns.move_legend(g, "upper left", bbox_to_anchor=(.85, .6), title='Methods')
plt.show(block=True)
