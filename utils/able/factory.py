import os, sys
import click
import json
import math
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), "src"))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from dataparser import scenario
from utils import helper
from utils import map_helper

from testing_engines.gflownet.path_config import path_args
from testing_engines.gflownet.lib.monitor import Monitor
from testing_engines.gflownet.generator.pre_process.transform_actions import decode, encode
from testing_engines.gflownet.GFN_Fuzzing import generate_scenarios_batch, get_history_scenarios

import testcase_conversion


class AbleFactory:
    def __init__(self, history, session, rule: str) -> None:
        self.map_info = map_helper.get_map_info(os.path.join(os.path.dirname(__file__), "../../map/") + "/san_francisco.json")
        self.spec = self.prepare_spec(rule)
        self.history_data = history
        self.session = session
        self.raw_scenario = scenario.scenario_parser(path_args.raw_template_path.format(session))

    @classmethod
    def prepare_spec(cls, rule: str):
        if rule == "traffic_light_red":
            translated_statement = "(eventually (((trafficLightAheadcolor==1) and ((stoplineAhead<=2.0 or junctionAhead<=2.0)) and (not (direction==2))) and (always[0,3] ((speed>=0.5)))))"
        elif rule == "traffic_light_yellow":
            translated_statement = "(eventually (((trafficLightAheadcolor==2) and stoplineAhead<=3.5 and (not stoplineAhead<=0.5) and currentLanenumber>0) and (always[0,3] ((speed>=0.5)))))"
        elif rule == "overtaking":
            translated_statement = "(eventually ((isOverTaking==1 and not (((turnSignal==1) and ((((eventually[-1,2] (hornOn==1))) or ((((highBeamOn==1 and ((highBeamOn==1 -> ((eventually[0,2] (lowBeamOn==1))))))) or ((lowBeamOn==1 and ((lowBeamOn==1 -> ((eventually[0,2] (highBeamOn==1)))))))))))) and ((eventually[0,10] (((turnSignal==2) and (((((isLaneChanging==1) -> (NearestNPCAhead<=5.0))) and (isLaneChanging==1)))))))))))"
        elif rule == "car_stop_at_crosswalk":
            translated_statement = "(eventually ((((((crosswalkAhead<=3.0 or junctionAhead<=3.0)) and NPCAheadAhead<=3.0) and (eventually[0,2] (NPCAheadspeed<0.5))) and (always[0,2] ((speed>=0.5))))))"
        elif rule == "park_at_crosswalk":
            translated_statement = "eventually ((crosswalkAhead<=0.1 or junctionAhead<=0.1) and (always[0,2] (speed<0.5)))"
        elif rule == "park_near_crosswalk":
            translated_statement = "eventually ((crosswalkAhead<=6.1 or junctionAhead<=6.1) and (always[0,2] (speed<0.5)))"
        elif rule == "park_near_signal":
            translated_statement = "eventually (signalAhead<=9.14 and (always[0,2] (speed<0.5)))"
        elif rule == "park_near_stop_sign":
            translated_statement = "eventually (stopSignAhead<=9.14 and (always[0,2] (speed<0.5)))"
        elif rule == "pedestrian_at_crosswalk":
            translated_statement = "eventually ((junctionAhead<=3.0 and PriorityPedsAhead==1) and (always[0,2] (speed>=0.5)))"
        elif rule == "pedestrian_at_crosswalk_turning_side":
            translated_statement = "eventually ((junctionAhead<=3.0 and PriorityPedsAhead==1) and (always[0,2] (speed>=0.5)))"
        else:
            raise ValueError("Rule not supported")

        single_specification = lambda: None
        single_specification.translated_statement = translated_statement
        return single_specification

    @classmethod
    def prepare_template(cls, seed, session):
        raw_scenario = scenario.scenario_parser(seed)
        map_info = map_helper.get_map_info(os.path.join(os.path.dirname(__file__), "../../map/") + "/san_francisco.json")
        template = testcase_conversion.convert_to_template(raw_scenario, map_info, session)
        return template

    @classmethod
    def prepare_history_data(cls, data_path, rule, session_name=None):
        """
        convert a directory of seed/trace to history data
        - .
            - queue
                - 1
                - 2
                - ...
            - trace
                - 1.txt
                - 2.txt
                - ...
        """
        if not session_name:
            session_name = "test"
            print("Session name not provided, using test as default")

        if not os.path.exists(data_path):
            sys.exit("Directory does not exist")

        queue_path = os.path.join(data_path, "queue")
        trace_path = os.path.join(data_path, "trace")

        if not os.path.exists(queue_path) or not os.path.exists(trace_path):
            sys.exit("Queue or trace directory does not exist")

        batch_testdata = []
        map_info = map_helper.get_map_info(os.path.join(os.path.dirname(__file__), "../../map/") + "/san_francisco.json")
        spec = cls.prepare_spec(rule)
        for seed in os.listdir(queue_path):
            raw_scenario = scenario.scenario_parser(os.path.join(queue_path, seed))
            trace = helper.get_trace(os.path.join(trace_path, seed + ".txt"))

            output_trace = testcase_conversion.convert_to_output_trace(raw_scenario, trace, map_info, session_name)
            if output_trace["trace"] == []:
                continue
            monitor = Monitor(output_trace, spec)
            robustness = monitor.continuous_monitor()
            output_trace["robustness"] = [-100000.0, robustness]

            batch_testdata.append(output_trace)

        batch_testdata_seq = []
        idx = 0
        for item in batch_testdata:
            ScenarioName = item["ScenarioName"] + "_new_" + str(idx)
            item["robustness"][0] = math.exp(-max(list(item["robustness"])))
            action_seq = encode(item)
            action_seq["ScenarioName"] = ScenarioName
            batch_testdata_seq.append(action_seq)
            idx += 1

        return batch_testdata_seq

    def merge_newdata_into_dataset(self, history_data, batch_testdata, session):
        # encode the newly-generated scenarios to action sequence
        batch_testdata_seq = []
        idx = 0
        for item in batch_testdata:
            ScenarioName = item["ScenarioName"] + "_new_" + str(idx)
            item["robustness"][0] = -max(list(item["robustness"]))
            action_seq = encode(item)
            action_seq["ScenarioName"] = ScenarioName
            batch_testdata_seq.append(action_seq)
            idx += 1
        # remove_useless_action(batch_testdata_seq, session)
        # update reward values in the new set
        history_data.extend(batch_testdata_seq)
        for item in history_data:
            # item["robustness"][0] = new_reward_function(item, specs_covered_flag)
            # item["robustness"][0] = max_robust_function(item, specs_covered_flag)
            item["robusness"][0] = math.exp(-max(list(item["robustness"][1:])))
        # For debug
        dataset_path = path_args.in_process_dataset_path.format(session)
        with open(dataset_path, "w") as wf:
            json.dump(history_data, wf, indent=4)

        return history_data

    def mutate(self):
        new_testcase_batch_total = []
        for b_index in range(1):
            ### generate new batches
            start = datetime.now()
            new_testcase_batch = generate_scenarios_batch(self.history_data, self.session)
            end = datetime.now()
            print("learning cost: {}".format(end - start))

            ### get all generate batches
            for index, batch in enumerate(new_testcase_batch):
                new_testcase_batch_total.append(batch)

                ### store new batches
                new_scenario = testcase_conversion.update_scenario_from_testcase(self.raw_scenario, batch, self.map_info)
                seed_path = "/home/apollo/VioHawk/utils/able/temp_new_seed/seed_" + str(b_index) + "_" + str(index) + ".json"
                new_scenario.store(seed_path)

                ### run apollo+simulator to get trace for robustness
                # batch_robustness = run(batch，self.rule)
                # new_testcase_batch_robustness.append(batch_robustness)

            ### merge new batchs to history data
            # self.history_data = self.merge_newdata_into_dataset(self.history_data, new_testcase_batch, self.session)
        return new_testcase_batch_total


@click.group()
def cli():
    pass


@cli.command()
@click.option("-d", "--data_path", type=click.Path(file_okay=False, exists=True), required=True, help="Path to the directory of seed/trace")
@click.option("-r", "--rule", type=str, required=True, help="Rule to be used")
@click.option("-s", "--session_name", type=str, help="Session name")
def history(data_path, rule, session_name):
    """prepare history data"""
    history_data = AbleFactory.prepare_history_data(data_path, rule, session_name)
    history_path = path_args.train_data_path.format(session_name)
    with open(history_path, "w") as wf:
        json.dump(history_data, wf, indent=4)


@cli.command()
@click.option("-f", "--seed", type=str, required=True, help="Seed")
@click.option("-s", "--session", type=str, required=True, help="Session name")
def template(seed, session):
    """prepare template"""
    template = AbleFactory.prepare_template(seed, session)
    template_path = path_args.template_path.format(session)
    with open(template_path, "w") as wf:
        json.dump(template, wf, indent=4)

    # copy seed file to raw_template_path
    raw_template_path = path_args.raw_template_path.format(session)
    os.system("cp {} {}".format(seed, raw_template_path))


@cli.command()
@click.option("-s", "--session", type=str, required=True, help="Session name")
def mutate(session):
    """mutate history data"""
    history = get_history_scenarios(session)
    factory = AbleFactory(history, session, "traffic_light_red")
    factory.mutate()


if __name__ == "__main__":
    cli()
