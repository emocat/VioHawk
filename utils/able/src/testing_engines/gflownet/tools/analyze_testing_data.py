import csv
import json
import math
import os

from testing_engines.gflownet.GFN_Fuzzing import load_specifications
from testing_engines.gflownet.lib.monitor import Monitor

"""compute the total covered specs in all sessions, and compute their difficulty value.
"""

def compute_difficulty_bk():

    with open("/home/xdzhang/work/shortgun/testing_engines/gflownet/rawdata/specs/spec_data.json") as file:
        specs = json.load(file)
    del specs["all_rules"]
    #
    # belong_to = "my_"
    belong_to = "lawbreaker_"

    all_specs = list(specs.values())
    # sessions = ['Intersection_with_Double-Direction_Roads', 'lane_change_in_the_same_road']
    sessions = ['Single-Direction-1']
    # data_path = '/data/xdzhang/apollo7/22-07-31-active-2*64/{}/data'
    # data_path = "/data/DATA-For-Traffic-Laws/T-Junction-Apollo6.0/{}/data"
    data_path = "/data/xdzhang/apollo7/lawbreaker-8-2/{}/data"
    oracle_list = []
    total_data_difficulty = dict()
    for session in sessions:
        print("Start analyzing session {}".format(session))
        covered_specs = []
        covered_num = 0
        data_dir = data_path.format(session)
        for root, _, data_files in os.walk(data_dir):
            for data_file in data_files:
                if not data_file.endswith('.json'):
                    continue
                with open(os.path.join(root, data_file)) as f:
                    data = json.load(f)
                    monitor = Monitor(data, 0)
                    for spec in all_specs:
                        rub_spec = monitor.continuous_monitor2(spec)
                        if rub_spec >= 0:
                            if spec in total_data_difficulty.keys():
                                total_data_difficulty[spec]["tests_num"] += 1
                                if session not in total_data_difficulty[spec]["sessions"]:
                                    total_data_difficulty[spec]["sessions"].append(session)
                            else:
                                total_data_difficulty[spec] = dict()
                                total_data_difficulty[spec]["tests_num"] = 1
                                total_data_difficulty[spec]["sessions"] = [session]
                            covered_num += 1
                            if spec not in covered_specs:
                                covered_specs.append(spec)
    for key, value in total_data_difficulty.items():
        total_data_difficulty[key]["difficulty"] = math.exp(128/(100*total_data_difficulty[key]["tests_num"] * len(total_data_difficulty[key]["sessions"])))
    total_data = sorted(total_data_difficulty.items(), key = lambda item : item[1]["difficulty"])
    with open(belong_to + 'total_data_difficulty.json', 'w', encoding='utf-8') as f:
        json.dump(total_data, f, ensure_ascii=False, indent=4)

def compute_difficulty_single_session(belong_to, data_path_form, session):
    with open("/home/xdzhang/work/shortgun/testing_engines/gflownet/rawdata/specs/spec_data.json") as file:
        specs = json.load(file)
    del specs["all_rules"]
    all_specs = list(specs.values())
    violation_times = dict()
    covered_specs = []
    increase_table = dict()
    increase_table[0] = 0
    index = 1
    print("Start analyzing session {}".format(session))
    data_dir = data_path_form.format(session)
    for root, _, data_files in os.walk(data_dir):
        for data_file in data_files:
            if not data_file.endswith('.json'):
                continue
            with open(os.path.join(root, data_file)) as f:
                data = json.load(f)
                monitor = Monitor(data, 0)
                for spec in all_specs:
                    rub_spec = monitor.continuous_monitor2(spec)
                    if rub_spec >= 0:
                        if spec not in covered_specs:
                            covered_specs.append(spec)
                        if spec in violation_times.keys():
                            violation_times[spec] += 1
                        else:
                            violation_times[spec] = 1
            increase_table[index] = len(covered_specs)
            index += 1

    result = []
    for key, value in violation_times.items():
        difficulty = 1/value
        result.append([key, belong_to, difficulty])
    save_path = "difficulty/{}_{}.json".format(belong_to, session)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    increase_data = []
    for key, value in increase_table.items():
        increase_data.append([belong_to, key, value])
    original_len = len(increase_data)
    if original_len < 512:
        for _ in range(512 - original_len):
            last = increase_data[-1]
            increase_data.append([last[0], last[1]+1, last[2]])

    return covered_specs, result, increase_data


def compute_difficulty(version):
    my_sessions = ['double_direction', 'lane_change', 'single_direction', 't_junction']
    # my_sessions = ['double_direction']
    lb_sessions = ['Intersection_with_Double-Direction_Roads', 'lane_change_in_the_same_road', 'Single-Direction-1', 'T-Junction01']
    # lb_sessions = ['Intersection_with_Double-Direction_Roads']

    difficulty_plot_path = 'plot_data/{}/difficulty_plot_data.csv'.format(version)
    with open(difficulty_plot_path, 'w') as f:
        csv_write = csv.writer(f)
        head = ['spec', 'Methods', 'Difficulty Degree', 'Newly Discovered', 'Session']
        csv_write.writerow(head)

    increase_path = 'plot_data/{}/increase_plot_data.csv'.format(version)
    with open(increase_path, 'w') as f:
        csv_write = csv.writer(f)
        head = ['Methods', '#Testing Scenarios', '#Violation Constraints', 'Session']
        csv_write.writerow(head)

    my_data_path_form = ''
    lb_data_path_form = ''
    if version == "apollo7":
        my_data_path_form = '/data/xdzhang/apollo7/best/{}/data'
        lb_data_path_form = "/data/xdzhang/apollo7/lawbreaker-8-2/{}/data"
    if version == "apollo6":
        my_data_path_form = '/data/xdzhang/apollo6/shortgun-8-7/{}/data'
        lb_data_path_form = "/data/xdzhang/apollo6/lawbreaker/{}/data"
    for i in range(4):
        belong_to = 'shortgun'
        session = my_sessions[i]
        shortgun_set, my_reuslt, my_increase_data = compute_difficulty_single_session(belong_to, my_data_path_form, session)

        belong_to = 'lawbreaker'
        session = lb_sessions[i]
        lb_set, lb_reuslt, lb_increase_data = compute_difficulty_single_session(belong_to, lb_data_path_form, session)

        my_reuslt.extend(lb_reuslt)
        for item in my_reuslt:
            if item[0] in shortgun_set and item[0] not in lb_set:
                item.append('Yes')
            else:
                item.append('No')
            item.append(my_sessions[i])

        with open(difficulty_plot_path, 'a+') as f:
            csv_write = csv.writer(f)
            csv_write.writerows(my_reuslt)

        my_increase_data.extend(lb_increase_data)
        for item in my_increase_data:
            item.append(my_sessions[i])
        with open(increase_path, 'a+') as f:
            csv_write = csv.writer(f)
            csv_write.writerows(my_increase_data)

def compute_coverage(apollo_version, belong_to, data_path, sessions):
    with open("../../../Specification/violation_formulae.json") as file:
        specs = json.load(file)
    del specs["all_rules"]
    #
    all_specs = list(specs.values())
    total_data_cover_by_session = dict()
    for session in sessions:
        print("Start analyzing session {}".format(session))
        covered_specs = []
        covered_num = 0
        data_dir = data_path.format(session)
        print("Current path {}".format(data_dir))
        for root, _, data_files in os.walk(data_dir):
            for data_file in data_files:
                if not data_file.endswith('.json'):
                    continue
                with open(os.path.join(root, data_file)) as f:
                    data = json.load(f)
                    monitor = Monitor(data, 0)
                    for spec in all_specs:
                        if spec in covered_specs:
                            continue
                        rub_spec = monitor.continuous_monitor2(spec)
                        if rub_spec >= 0:
                            covered_num += 1
                            covered_specs.append(spec)
        total_data_cover_by_session[session] = covered_specs
        print("Session {}, covered_num: {}, covered_specs: {}".format(session, covered_num, covered_specs))
    path = "coverage/{}/{}coverage_as_session.json".format(apollo_version, belong_to)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(total_data_cover_by_session, f, ensure_ascii=False, indent=4)

def verify_one(path, spec):
    with open(path) as f:
        data = json.load(f)
        monitor = Monitor(data, 0)
        rub_spec = monitor.continuous_monitor2(spec)
        if rub_spec >= 0:
            return True
        return False

def verify_in_which_files(data_dir, spec):
    result = []
    for root, _, data_files in os.walk(data_dir):
        for data_file in data_files:
            if not data_file.endswith('.json'):
                continue
            with open(os.path.join(root, data_file)) as f:
                data = json.load(f)
                monitor = Monitor(data, 0)
                rub_spec = monitor.continuous_monitor2(spec)
                if rub_spec >= 0:
                    print(os.path.join(root, data_file))
                    result.append(os.path.join(root, data_file))
    return result

def verify_in_which_file(data_dir, spec):
    file = ''
    for root, _, data_files in os.walk(data_dir):
        for data_file in data_files:
            if not data_file.endswith('.json'):
                continue
            with open(os.path.join(root, data_file)) as f:
                data = json.load(f)
                monitor = Monitor(data, 0)
                rub_spec = monitor.continuous_monitor2(spec)
                if rub_spec >= 0:
                    print(os.path.join(root, data_file))
                    file = os.path.join(root, data_file)
                    break
    return file
def compute_robustness():
    specs = ['eventually(((direction==2)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))',
             'eventually(((direction==2)and(PriorityPedsAhead==1))and(always[0,2](not(speed<0.5))))',
             'eventually(((direction==1)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))',
             'eventually(((direction==1)and(PriorityPedsAhead==1))and(always[0,2](not(speed<0.5))))']
    path = "/data/xdzhang/apollo7/best/lane_change/data/result17-08-2022-18-32-48.json"
    for spec in specs:
        with open(path) as f:
            data = json.load(f)
            monitor = Monitor(data, 0)
            rub_spec = monitor.continuous_monitor2(spec)
            print(spec, rub_spec)

def coverage():
    my_sessions = ['double_direction', 'lane_change', 'single_direction', 't_junction']
    # ################################### apollo7
    apollo7_data_path_my = '/data/xdzhang/apollo7/active+max/{}/data'
    compute_coverage("apollo7", "my_active+max_", apollo7_data_path_my, my_sessions)

    apollo7_data_path_my = '/data/xdzhang/apollo7/shortgun-no-active/{}/data'
    compute_coverage("apollo7", "my_inactive+new_", apollo7_data_path_my, my_sessions)

    # lb_sessions = ['Intersection_with_Double-Direction_Roads', 'lane_change_in_the_same_road', 'Single-Direction-1', 'T-Junction01']
    # # lb_sessions = ['T-Junction01']
    # apollo7_data_path_lb = "/data/xdzhang/apollo7/lawbreaker-8-2/{}/data"
    # compute_coverage("apollo7", "lawbreaker_", apollo7_data_path_lb, lb_sessions)

    # ################################### apollo6
    # my_sessions = ['double_direction', 'lane_change', 'single_direction', 't_junction']
    # apollo6_data_path_my = "/data/xdzhang/apollo6/shortgun-8-7/{}/data"
    # compute_coverage("apollo6", "my_", apollo6_data_path_my, my_sessions)
    #
    # lb_sessions = ['Intersection_with_Double-Direction_Roads', 'lane_change_in_the_same_road', 'Single-Direction-1', 'T-Junction01']
    # # lb_sessions = ['T-Junction01']
    # apollo6_data_path_lb = "/data/xdzhang/apollo6/lawbreaker/{}/data"
    # compute_coverage("apollo6", "lawbreaker_", apollo6_data_path_lb, lb_sessions)

def get_validate_cases(session, specs):
    data_path_form = "/data/xdzhang/apollo7/best/{}/data".format(session)
    scene = dict()
    for s in specs:
        print(s)
        files = verify_in_which_files(data_path_form, s)
        one_spec_to_sces = []
        for file in files:
            with open(file) as f:
                data = json.load(f)
                del data["groundTruthPerception"]
                del data["testFailures"]
                del data["testResult"]
                del data["minEgoObsDist"]
                del data["destinationReached"]
                del data["trace"]
                del data["completed"]
                one_spec_to_sces.append(data)
        scene[s] = one_spec_to_sces
        print("--------------")
    validate_test_path = "../validate/{}_new_covered.json".format(session)
    with open(validate_test_path, 'w', encoding='utf-8') as f:
        json.dump(scene, f, ensure_ascii=False, indent=4)

def validate():
    my_sessions = ['double_direction', 'lane_change', 'single_direction', 't_junction']
    spec_table = dict()
    specs_double_direction = ['eventually((((trafficLightAheadcolor==3)and(direction==1))and(Time>=20.0))and(not(lowBeamOn==1)))', 'eventually(((((trafficLightAheadcolor==3)and(direction==1))and(Time<=20.0))and(Time>=7.0))and(not(turnSignal==1)))', 'eventually((isOverTaking==1)and(always[0,10]((isLaneChanging==1)and(not(NearestNPCAhead<=5.0)))))', 'eventually((direction==1)and(not(turnSignal==1)))', 'eventually(((isLaneChanging==1)and(currentLanenumber>=2))and(PriorityNPCAhead==1))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))', 'eventually((((trafficLightAheadcolor==3)and(direction==1))and(Time>=20.0))and(not(turnSignal==1)))']
    specs_single_direction = ['eventually((((trafficLightAheadcolor==3)and(direction==1))and(Time<=7.0))and(not(lowBeamOn==1)))', 'eventually((((trafficLightAheadcolor==3)and(direction==1))and(Time>=20.0))and(not(lowBeamOn==1)))', 'eventually(((((trafficLightAheadcolor==3)and(direction==1))and(Time<=20.0))and(Time>=7.0))and(not(turnSignal==1)))', 'eventually((((trafficLightAheadcolor==3)and(direction==1))and(Time<=7.0))and(not(turnSignal==1)))', 'eventually((direction==1)and(not(turnSignal==1)))', 'eventually((direction==2)and(not(turnSignal==2)))', 'eventually(((direction==2)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))', 'eventually((((signalAhead==0)and(PriorityNPCAhead==1))and(junctionAhead<=1.0))and(always[0,2](not(speed<0.5))))', 'eventually((((trafficLightAheadcolor==3)and(direction==1))and(Time>=20.0))and(not(turnSignal==1)))']
    specs_lane_change = ['eventually(((direction==1)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))', 'eventually((direction==1)and(not(speed<=30)))', 'eventually(((direction==2)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))', 'eventually(((isLaneChanging==1)and(currentLanenumber>=2))and(PriorityNPCAhead==1))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(NPCAheadAhead<=0.5))']
    specs_t_junction = ['eventually((direction==1)and(not(turnSignal==1)))', 'eventually(((((trafficLightAheadcolor==3)and(direction==1))and(Time<=20.0))and(Time>=7.0))and(not(turnSignal==1)))', 'eventually((direction==2)and(not(turnSignal==2)))', 'eventually(((direction==2)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))']
    spec_table['double_direction'] = specs_double_direction
    spec_table['lane_change'] = specs_lane_change
    spec_table['single_direction'] = specs_single_direction
    spec_table['t_junction'] = specs_t_junction
    for session in my_sessions:
        print(session, "==========================================================")
        get_validate_cases(session, spec_table[session])

if __name__ == "__main__":
    coverage()
    # compute_difficulty("apollo7")
    # validate()
    # compute_robustness()
