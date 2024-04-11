import copy
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
            # print(msg['TYPE'])
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
                        print("---", spec, robustness)
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
def load_testcases(spec, session):
    validate_test_path = "validate/{}_new_covered.json".format(session)
    with open(validate_test_path) as file:
        json_obj = json.load(file)
        return json_obj[spec]

def load_testing_scenario(scenario_path):
    with open(scenario_path) as f:
        data = json.load(f)
        del data["groundTruthPerception"]
        del data["testFailures"]
        del data["testResult"]
        del data["minEgoObsDist"]
        del data["destinationReached"]
        del data["trace"]
        del data["completed"]
    return data

def load_testing_scenario_sunyang(scenario_path):
    with open(scenario_path) as f:
        data = json.load(f)
    return data

def load_specification(spec_name):
    spec_path = "/home/xdzhang/ABLE/Specification/violation_formulae.json"
    with open(spec_path) as file:
        specs = json.load(file)
        return specs[spec_name]


def load_specifications():
    with open(path_args.spec_path) as file:
        specs = json.load(file)
    del specs["all_rules"]
    table = dict()
    for idx, spec in enumerate(specs.values()):
        table[spec] = idx + 1
    return list(specs.values()), table

def load_target_specs():
    return ['eventually(((direction==1)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))', 'eventually((direction==1)and(not(speed<=30)))', 'eventually(((direction==2)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))', 'eventually(((isLaneChanging==1)and(currentLanenumber>=2))and(PriorityNPCAhead==1))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(NPCAheadAhead<=0.5))']



def test_scenario_batch(testcases, remained_specs, file_directory):
    covered_specs = list()
    for item in testcases[:]:
        reward = [-100000.0] * 82
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.gather(asyncio.gather(
                test_one_scenario(item, remained_specs, covered_specs, reward, directory=file_directory))))
        if len(covered_specs) == 1:
            break
    return covered_specs


def merge_newdata_into_dataset(history_data, batch_testdata, remained_specs, session):
    specs_covered_flag = [1]*81 # 1 stands for the corresponding spec is uncovered, otherwise.
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
        reward = 0.0
        robust = item["robustness"][1:]
        for i in range(81):
            if robust[i] >= 0:
                distance = 0
            else:
                distance = -robust[i]
            reward += (specs_weight[i]*specs_covered_flag[i] / (distance + 1.0))
        item["robustness"][0] = reward
        # item["robustness"][0] = -max(item["robustness"][1:])
    # For debug
    dataset_path = path_args.in_process_dataset_path.format(session)
    with open(dataset_path, 'w') as wf:
        json.dump(history_data, wf, indent=4)

    return history_data


def test_session(session, testcases, remained_specs):
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

    for _ in range(100):
        covered_specs = test_scenario_batch(testcases, remained_specs, log_direct)
        if len(covered_specs) != 0:
            print("Replay is successful.")
            break
        else:
            print("Continue....")

"""
" specs formula -> the index in the json file
"""
specs_to_index = dict()
specs_weight = [1]*81
active_learning_loop = 1


if __name__ == "__main__":
    start = datetime.now()
    sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
    session = 't_junction'
    buggy_testing_scenario = "sub_law_violation_5"
    # path = '/home/xdzhang/ABLE/testing_engines/gflownet/validate/apollo7/{}/{}.json'.format(session, buggy_testing_scenario)
    # new_testcases = load_testcases(target_spec, session)
    # testcase = load_testing_scenario(path)
    path = "/home/xdzhang/data/rerun_for_videos/T-Junction/hesitate_at_yellow_light3.json"
    testcase = load_testing_scenario_sunyang(path)
    target_spec = load_specification(buggy_testing_scenario)
    print(testcase)
    test_session(session, [testcase], [target_spec])
