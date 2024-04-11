import json
import math
import os

from testing_engines.gflownet.GFN_Fuzzing import new_reward_function, max_robust_function

if __name__ == "__main__":
    covered = [1] * 81
    # sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
    sessions = ['single_direction']
    for session in sessions:
        path = "../generator/data/testset/a_testset_for_{}.json".format(session)
        with open(path) as f:
            data = json.load(f)
            for item in data:
                # item["robustness"][0] = new_reward_function(item, covered)
                item["robustness"][0] = max_robust_function(item, covered)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)