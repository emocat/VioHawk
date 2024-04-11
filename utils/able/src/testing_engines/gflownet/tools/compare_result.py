import json
import math
import os

from testing_engines.gflownet.tools.analyze_testing_data import verify_in_which_file


def print_index(specs):
    ret = []
    for spec in specs:
        path = "../../../Specification/violation_formulae.json"
        with open(path) as f:
            all_specs = json.load(f)
            index = 0
            for key, value in all_specs.items():
                if spec == value:
                    ret.append(index)
                index += 1
    print(sorted(ret))

def get_index(spec):
    path = "../../../Specification/violation_formulae.json"
    with open(path) as f:
        all_specs = json.load(f)
        for key, value in all_specs.items():
            if spec == value:
                return key

def findoutTraces(version, session, specs):
    path = '/data/xdzhang/{}/shortgun-no-active/{}/data'.format(version, session)
    for spec in specs:
        print(spec)
        file = verify_in_which_file(path, spec)
        with open(file) as f:
            data = json.load(f)
        print("--------------")
        sub_law = get_index(spec)
        trace_path = "../../../ICSE2023_experimental_data/inactive+new/{}/{}".format(version, session)
        if not os.path.exists(trace_path):
            os.makedirs(trace_path)
        trace_file_name = "../../../ICSE2023_experimental_data/inactive+new/{}/{}/{}.json".format(version, session, sub_law)
        with open(trace_file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    my_sessions = ['double_direction', 'lane_change', 'single_direction', 't_junction']
    path_my = "coverage/apollo7/my_inactive+new_coverage_as_session.json"
    with open(path_my) as f:
        data_my = json.load(f)
    for session in my_sessions:
        findoutTraces('apollo7', session, set(data_my[session]))

def run():
    version = 'apollo6'
    path_lb = "coverage/{}/lawbreaker_coverage_as_session.json".format(version)
    path_my = "coverage/{}/my_coverage_as_session.json".format(version)
    print("compare between {} and {}".format(path_my, path_lb))
    with open(path_lb) as f:
        data_lb = json.load(f)
    with open(path_my) as f:
        data_my = json.load(f)

    print("For session double_direction -->")
    print("exist in mine but not in lawbreaker:")
    print("ABLE: {}".format(len(data_my["double_direction"])))
    print("lawbreaker: {}".format(len(data_lb["Intersection_with_Double-Direction_Roads"])))
    delta = set(data_my["double_direction"]).difference(set(data_lb["Intersection_with_Double-Direction_Roads"]))
    findoutTraces(version, "double_direction", set(data_lb["Intersection_with_Double-Direction_Roads"]))
    print(len(delta), delta)
    print_index(delta)
    print("exist in lawbreaker but not in mine:")
    delta = set(set(data_lb["Intersection_with_Double-Direction_Roads"]).difference(data_my["double_direction"]))
    print(len(delta), delta)

    print("--------------")

    print("For session single_direction -->")
    print("exist in mine but not in lawbreaker:")
    print("ABLE: {}".format(len(data_my["single_direction"])))
    print("lawbreaker: {}".format(len(data_lb["Single-Direction-1"])))
    delta = set(data_my["single_direction"]).difference(set(data_lb["Single-Direction-1"]))
    findoutTraces(version, "single_direction", set(data_lb["Single-Direction-1"]))
    print(len(delta), delta)
    print_index(delta)
    print("exist in lawbreaker but not in mine:")
    delta = set(set(data_lb["Single-Direction-1"]).difference(data_my["single_direction"]))
    print(len(delta), delta)

    print("--------------")

    print("For session lane_change -->")
    print("exist in mine but not in lawbreaker:")
    print("ABLE: {}".format(len(data_my["lane_change"])))
    print("lawbreaker: {}".format(len(data_lb["lane_change_in_the_same_road"])))
    delta = set(data_my["lane_change"]).difference(set(data_lb["lane_change_in_the_same_road"]))
    findoutTraces(version, "lane_change", set(data_lb["lane_change_in_the_same_road"]))
    print(len(delta), delta)
    print_index(delta)
    print("exist in lawbreaker but not in mine:")
    delta = set(set(data_lb["lane_change_in_the_same_road"]).difference(data_my["lane_change"]))
    print(len(delta), delta)


    #
    print("--------------")
    print("For session t_junction -->")
    print("exist in mine but not in lawbreaker:")
    print("ABLE: {}".format(len(data_my["t_junction"])))
    print("lawbreaker: {}".format(len(data_lb["T-Junction01"])))
    delta = set(data_my["t_junction"]).difference(set(data_lb["T-Junction01"]))
    findoutTraces(version, "t_junction", set(data_lb["T-Junction01"]))
    print(len(delta), delta)
    print_index(delta)
    print("exist in lawbreaker but not in mine:")
    delta = set(set(data_lb["T-Junction01"]).difference(data_my["t_junction"]))
    print(len(delta), delta)


    # ours = set(data_my["double_direction"]) | set(data_my["single_direction"]) | set(data_my["lane_change"])
    #        # | set(data_my["t_junction"])
    # print(len(ours), ours)
    #
    # lb = set(data_lb["Intersection_with_Double-Direction_Roads"]) | set(data_lb["Single-Direction-1"]) | set(data_lb["lane_change_in_the_same_road"])
    #      # | set(data_lb["T-Junction01"])
    # print(len(lb), lb)
    # print("================")
    # print(ours - lb)
    # print(lb - ours)