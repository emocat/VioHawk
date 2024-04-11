import copy
import math
import os
import shutil
import sys
import time
import websockets
import json
import asyncio
from datetime import datetime
import logging

from testing_engines.gflownet.generator.proxy.proxy_config import proxy_args
from testing_engines.gflownet.generator.proxy.train_proxy import train_proxy
from testing_engines.gflownet.generator.generative_model.main import generate_samples_with_gfn
from testing_engines.gflownet.generator.pre_process.transform_actions import decode, encode
from testing_engines.gflownet.lib.monitor import Monitor
from testing_engines.gflownet.path_config import path_args
from testing_engines.gflownet.tools.remove_useless_action import remove_useless_action


async def test_one_scenario(scenario_testcase, specs, covered_specs, reward, directory=None) -> object:
    uri = "ws://localhost:8000"  # The Ip and port for our customized bridge.
    async with websockets.connect(uri, max_size=300000000, ping_interval=None) as websocket:
        # Initialize files
        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
        await websocket.send(init_msg)
        while True:
            msg = await websocket.recv()
            msg = json.loads(msg)
            if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                if msg['DATA']:
                    logging.info('Running Scenario: {}'.format(scenario_testcase["ScenarioName"]))
                    send_command_msg = {'CMD': "CMD_NEW_TEST", 'DATA': scenario_testcase}
                    await websocket.send(json.dumps(send_command_msg))
                else:
                    time.sleep(3)
                    init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                    await websocket.send(init_msg)
            elif msg['TYPE'] == 'KEEP_SERVER_AND_CLIENT_ALIVE':
                send_msg = {'CMD': "KEEP_SERVER_AND_CLIENT_ALIVE", 'DATA': None}
                await websocket.send(json.dumps(send_msg))
            elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                print("Try to reconnect.")
                time.sleep(3)
                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                await websocket.send(init_msg)
            elif msg['TYPE'] == 'TEST_COMPLETED':
                output_trace = msg['DATA']
                dt_string = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                file = directory + '/data/result' + dt_string + '.json'
                with open(file, 'w') as outfile:
                    json.dump(output_trace, outfile, indent=2)
                logging.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                if not output_trace['destinationReached']:
                    with open(directory + '/Incompleted.txt', 'a') as f:
                        json.dump(scenario_testcase, f, indent=2)
                        f.write('\n')
                if len(output_trace['trace']) > 1:
                    if 'Accident!' in output_trace["testFailures"]:
                        with open(directory + '/AccidentTestCase.txt', 'a') as bug_file:
                            now = datetime.now()
                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                            string_index = "Time:" + dt_string + ", Scenario: " + scenario_testcase["ScenarioName"] + \
                                           ", Bug: " + str(output_trace["testFailures"]) + '\n'
                            bug_file.write(string_index)
                            json.dump(output_trace, bug_file, indent=2)
                            bug_file.write('\n')
                    monitor = Monitor(output_trace, 0)
                    for spec in specs:
                        if spec in covered_specs:
                            continue
                        robustness = monitor.continuous_monitor2(spec)
                        reward[specs_to_index[spec]] = robustness
                        if robustness < 0.0:
                            continue
                        covered_specs.append(spec)
                        with open(directory + '/violationTestCase.txt', 'a') as violation_file:
                            now = datetime.now()
                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                            string_index = "Time:" + dt_string + ". Scenario: " + scenario_testcase["ScenarioName"] + '\n'
                            violation_file.write(string_index)
                            string_index2 = "The detailed fitness values:" + str(robustness) + '\n'
                            violation_file.write(string_index2)
                            # bug_file.write(spec)
                            json.dump(output_trace, violation_file, indent=2)
                            violation_file.write('\n')

                elif len(output_trace['trace']) == 1:
                    logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                        output_trace['destinationReached'], output_trace['minEgoObsDist']))
                else:
                    logging.info("No trace for the test cases!")
                    with open(directory + '/NoTrace.txt', 'a') as f:
                        now = datetime.now()
                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        f.write("Time: {}, Scenario: {}".format(dt_string, scenario_testcase["ScenarioName"]))
                        json.dump(scenario_testcase, f, indent=2)
                        f.write('\n')
                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                await websocket.send(init_msg)
                break
            else:
                print("Incorrect response.")
                break


def get_history_scenarios(session):
    with open(path_args.train_data_path.format(session)) as file:
        dataset = json.load(file)
    return dataset


def generate_scenarios_batch(dataset, session):
    # Train model to generate new scenarios to files
    while True:
        train_proxy(proxy_args, dataset, session)
        new_batch = generate_samples_with_gfn(dataset, session)
        if len(new_batch) != 1:
            break
    # For debug
    with open(path_args.new_batch_path.format(session), 'w', encoding='utf-8') as file:
        json.dump(new_batch, file, indent=4)
    #
    test_cases_batch = []
    for item in new_batch:
        test_cases_batch.append(decode(item, session))
    return test_cases_batch

def debug_new_batch(session):
    with open(path_args.new_batch_path.format(session)) as file:
        dataset = json.load(file)
    #
    test_cases_batch = []
    for item in dataset:
        test_cases_batch.append(decode(item, session))
    return test_cases_batch

"""
For debugging single scenario
"""
def generate_one_scenario():
    test_cases = []
    one_testcase = "generator/data/one_testcase.json"
    with open(one_testcase) as file:
        json_obj = json.load(file)
        if isinstance(json_obj, list):
            test_cases.extend(json_obj)
        else:
            test_cases.append(json_obj)
    return test_cases


def load_specifications():
    with open(path_args.spec_path) as file:
        specs = json.load(file)
    del specs["all_rules"]
    table = dict()
    for idx, spec in enumerate(specs.values()):
        table[spec] = idx + 1
    return list(specs.values()), table


def test_scenario_batch(testcases, remained_specs, file_directory):
    covered_specs = list()
    new_dataset = []
    # print("Uncovered specs before batch {}: {}".format(batch_no, len(remain_specs)))
    # just testing half of the batch.
    for item in testcases[:]:
        reward = [-100000.0] * 82
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.gather(asyncio.gather(
                test_one_scenario(item, remained_specs, covered_specs, reward, directory=file_directory))))
        item["robustness"] = reward
        logging.info("Current covered specs: {} until the scenario {}".format(len(covered_specs), item['ScenarioName']))
        new_dataset.append(item)
    # remove covered specs from remained_specs
    for cs in covered_specs:
        remained_specs.remove(cs)
    # print("Uncovered specs after batch {}: {}".format(batch_no, len(remain_specs)))
    return covered_specs, new_dataset

def new_reward_function(item, specs_covered_flag):
    reward = 0.0
    robust = item["robustness"][1:]
    for i in range(81):
        if robust[i] >= 0:
            distance = 0
        else:
            distance = -robust[i]
        reward += (specs_weight[i] * specs_covered_flag[i] / (distance + 1.0))
    return reward

def max_robust_function(item, specs_covered_flag):
    condidates = []
    robust = item["robustness"][1:]
    for i in range(81):
        if specs_covered_flag[i] == 1:
            condidates.append(robust[i])
    return math.exp(max(condidates))

def merge_newdata_into_dataset(history_data, batch_testdata, remained_specs, session):
    specs_covered_flag = [1]*81 # 1 stands for the corresponding spec is uncovered, otherwise covered.
    all_specs, _ = load_specifications()
    for item in all_specs:
        if item in remained_specs:
            specs_covered_flag[specs_to_index[item] - 1] = 1
        else:
            specs_covered_flag[specs_to_index[item] - 1] = 0

    # encode the newly-generated scenarios to action sequence
    batch_testdata_seq = []
    idx = 0
    for item in batch_testdata:
        ScenarioName = item["ScenarioName"] + "_new_" + str(idx)
        item['robustness'][0] = -max(list(item['robustness']))
        action_seq = encode(item)
        action_seq["ScenarioName"] = ScenarioName
        batch_testdata_seq.append(action_seq)
        idx += 1
    remove_useless_action(batch_testdata_seq, session)
    # update reward values in the new set
    history_data.extend(batch_testdata_seq)
    for item in history_data:
        # item["robustness"][0] = new_reward_function(item, specs_covered_flag)
        item["robustness"][0] = max_robust_function(item, specs_covered_flag)
    # For debug
    dataset_path = path_args.in_process_dataset_path.format(session)
    with open(dataset_path, 'w') as wf:
        json.dump(history_data, wf, indent=4)

    return history_data


def test_session(session, total_specs_num, remained_specs):
    log_direct = path_args.test_result_direct.format(session)
    # Set testing result or data paths
    if not os.path.exists(log_direct):
        os.makedirs(log_direct)
    else:
        shutil.rmtree(log_direct)
    if not os.path.exists(log_direct + '/data'):
        os.makedirs(log_direct + '/data')
    # Set logger
    logging_file = log_direct + '/test.log'
    file_handler = logging.FileHandler(logging_file, mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.INFO, handlers=[stdout_handler, file_handler],
                        format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logging.info("Current Session: {}".format(session))
    # Initialize Batch_0
    history_data = get_history_scenarios(session)
    # Active learning loop
    covered_specs = list()
    for b_index in range(active_learning_loop):
        # apollo_pid = launch_apollo()
        # time.sleep(55)
        # print("Apollo launching success.")
        start = datetime.now()
        # new_testcase_batch = generate_scenarios_batch(history_data, session)
        new_testcase_batch = generate_one_scenario()
        # new_testcase_batch = debug_new_batch(session)
        end = datetime.now()
        logging.info("learning cost: {}".format(end - start))

        batch_covered_specs, batch_testdata = test_scenario_batch(new_testcase_batch, remained_specs, log_direct)
        coverage_rate = 1 - len(remained_specs) / total_specs_num
        logging.info("Batch index: {}, generating new testcases: {}, total coverage rate: {}/{} = {}, "
                     "new covered predicates: {}\n".format(b_index, len(new_testcase_batch),
                                                           (total_specs_num - len(remained_specs)),
                                                           total_specs_num, coverage_rate, batch_covered_specs))
        covered_specs.extend(batch_covered_specs)
        history_data = merge_newdata_into_dataset(history_data, batch_testdata, remained_specs, session)
        # stop_apollo(apollo_pid)
    return covered_specs


"""
" specs formula -> the index in the json file
"""
specs_to_index = dict()
specs_weight = [1]*81
active_learning_loop = 4


if __name__ == "__main__":
    start = datetime.now()
    # sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
    sessions = ['double_direction']
    # all_specs and specs_to_index have the same ordering for each spec
    all_specs, specs_to_index = load_specifications()
    total_specs_num = len(all_specs)
    all_covered_specs = list()
    for session in sessions:
        remind_specs = copy.deepcopy(all_specs)
        session_covered_specs = test_session(session, total_specs_num, remind_specs)
        all_covered_specs.extend(session_covered_specs)
        logging.info("Session: {}, total coverage rate: {}/{} = {}, new covered predicates: {}\n".format(session,
           len(all_covered_specs), total_specs_num, len(all_covered_specs) / total_specs_num, session_covered_specs))
    #
    end = datetime.now()
    result_info = "Finished, total coverage rate: {}/{} = {}, total time cost: {}, the covered predicates: {}\n".format(
        len(all_covered_specs), total_specs_num, len(all_covered_specs)/total_specs_num, (end - start), all_covered_specs)
    logging.info(result_info)
    print(result_info)