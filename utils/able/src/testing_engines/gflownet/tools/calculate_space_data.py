import json
import math
import os

if __name__ == "__main__":
    sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
    for session in sessions:
        path = "../generator/data/action_space_0.5_cartype/space_for_{}.json".format(session)
        with open(path) as f:
            data = json.load(f)
        print("--------------------------------------")
        print(session)
        print("length: {}".format(len(data)))
        multiple = 1
        for key, value in data.items():
            multiple *= len(value)
        print("space: {}".format("{:.1e}".format(multiple)))
    print("===============================================")
    for session in sessions:
        path = "../generator/data/action_space_0.5_cartype/space_for_{}.json".format(session)
        with open(path) as f:
            data = json.load(f)
        print("--------------------------------------")
        print(session)
        print("length: {}".format(len(data)))
        multiple = 1
        for key, value in data.items():
            multiple *= len(value)
        print("space: {}".format("{:.1e}".format(multiple)))