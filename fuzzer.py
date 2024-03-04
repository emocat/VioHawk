# coding=utf-8
# !/usr/bin/env python3
"""
Entry point of the apollo-fuzzer
"""
import os

import click
import timeout_decorator
import time
import subprocess
import numpy as np

import config as _Config
import logger as _Logger

import mutator as _Mutator
import dataparser as _Parser
import utils.lawbreaker as _Lawbreaker
import utils.avfuzzer as _AVFuzzer
import utils.drivefuzz as _DriveFuzz

from run_vse import VSERunner

LOG = _Logger.get_logger(_Config.__prog__)


class Fuzzer:
    def __init__(self, _corpus, _workdir, _map, _strategy, _rule):
        self.corpus = _Parser.corpus_parser(_corpus)
        self.workdir = _workdir
        self.map = _map
        self.strategy = _strategy
        self.rule = _rule
        self.init_workdir()

        # the seed queue
        self.population = []
        # seeds that can trigger collision
        self.collisions = []
        # testcases that have already been executed, used for testcase deduplication
        self.hashes = set([])

        self.simtime = 0
        self.env = os.environ.copy()
        self.env["DISPLAY"] = ":0"

    def init_workdir(self):
        if os.listdir(self.workdir):
            LOG.error("Working Directory Not Empty!")
            exit(-1)

        os.mkdir(self.workdir + "/queue")
        os.mkdir(self.workdir + "/collision")
        os.mkdir(self.workdir + "/violation")
        os.mkdir(self.workdir + "/trace")
        f = open(self.workdir + "/info", "w")
        f.close()

    def save_scenario_trace(self, seed):
        trace_path = "{}/trace/{}.txt".format(self.workdir, seed.get_hash())
        os.system("sleep 1 && cp ~/Build_Local/2021.2-wise/in.txt.gz /tmp")
        os.system("gunzip -f /tmp/in.txt.gz")
        os.system("mv /tmp/in.txt {}".format(trace_path))
        return trace_path

    def restart_simulation(self):
        subprocess.run(
            [
                "docker",
                "exec",
                "-u",
                "apollo",
                "-d",
                "apollo_dev_apollo",
                "./restart_dreamview_bridge.sh",
            ]
        )
        subprocess.run(["/usr/bin/zsh", "-c", "resim"])
        time.sleep(18)

    def run_instance(self, _seed, _save=True):
        # restart simulation every 30m
        if time.time() - self.simtime >= 1800:
            LOG.info("Restart LGSVL simulation")
            self.restart_simulation()
            self.simtime = time.time()

            LOG.info("running seed once to init environment")
            self.run_instance(_seed, _save=False)

        # check if it is a already-verified testcase
        if _seed.get_hash() in self.hashes:
            LOG.info("Duplicate seed: {}".format(_seed.get_hash()))
            return None, None

        # run a seed with lgsvl simulation
        vse_runner = VSERunner(_seed, _sensor_conf=_Config.SIM_SENSOR_CONF)
        try:
            vse_runner.run(30)
        except timeout_decorator.timeout_decorator.TimeoutError:
            LOG.info("vse_runner is timeout!")
            self.simtime = -1

        if not _save:
            return None, None

        # save scenario data
        trace_path = self.save_scenario_trace(_seed)

        # store collision seed
        if vse_runner.is_collision:
            _seed.store(self.workdir + "/collision/" + str(_seed.get_hash()))
            self.collisions.append(_seed)
            return None, None

        # calculate feedback score
        try:
            mutator = _Mutator.create_mutator(_seed, trace_path, self.map, self.rule)
            res = mutator.compute_dangerous_score()
        except ValueError as e:
            LOG.info("ValueError: {}".format(e))
            return None, None
        except AssertionError as e:
            LOG.info("AssertionError: {}".format(e))
            return None, None
        except IndexError as e:
            LOG.info("IndexError: {}".format(e))
            return None, None

        if res == -1:
            _seed.store(self.workdir + "/violation/" + str(_seed.get_hash()))
            exit(-1)

        if self.strategy == "viohawk":
            score = res
            mutator = mutator
        elif self.strategy == "lawbreaker":
            factory = _Lawbreaker.LawBreakerFactory(_seed, trace_path, self.rule)
            score = factory.calc_feedback()
            mutator = factory
        elif self.strategy == "avfuzzer":
            factory = _AVFuzzer.AVFuzzerFactory(_seed, trace_path, self.rule)
            score = factory.calc_feedback()
            mutator = factory
        elif self.strategy == "drivefuzz":
            factory = _DriveFuzz.DriveFuzzFactory(_seed, trace_path, self.rule)
            score = factory.calc_feedback()
            mutator = factory
        else:
            LOG.error("Unknown strategy: {}".format(self.strategy))
            exit(-1)

        LOG.info("Score: " + str(score))
        return mutator, score

    def population_add(self, _seed):
        scenario, _ = _seed
        # self.population.append(_seed)
        self.population.insert(0, _seed)

        if self.strategy in ["lawbreaker", "drivefuzz", "avfuzzer"]:
            self.population.sort(key=lambda x: x[0].score, reverse=False)
            self.population = self.population[:20]

        scenario.store(self.workdir + "/queue/" + str(scenario.get_hash()))

    def population_get(self) -> (_Parser.scenario.Scenario, _Mutator.Mutator):
        def softmax_with_temperature(data, temperature=1.0):
            scaled_data = data / temperature
            exp_data = np.exp(scaled_data - np.max(scaled_data))
            return exp_data / np.sum(exp_data)

        if self.strategy == "viohawk":
            energy = list(map(lambda seed: seed[0].score, self.population))
            energy = np.array(energy)
            temperature = 1 / len(self.population)
            norm_energy = softmax_with_temperature(energy, temperature=temperature)
            idx = np.random.choice(len(self.population), p=norm_energy)
            seed_pool = list(
                "{}({:.2})".format(self.population[i][0].score, norm_energy[i]) for i in range(len(self.population))
            )
        else:
            idx = np.random.choice(len(self.population))
            seed_pool = list("{}".format(self.population[i][0].score) for i in range(len(self.population)))

        seed = self.population[idx]
        LOG.info("seed pool: {}".format(seed_pool))
        LOG.info("get seed score: {}".format(seed[0].score))
        return seed

    def population_dup(self, score):
        if self.strategy == "viohawk":
            count_zero = 0
            for seed in self.population:
                if score != 0 and abs(seed[0].score - score) < 0.005:
                    return True
                if score == 0:
                    count_zero += 1
            if count_zero > 20:
                return True
        return False

    def execute(self):
        # first initialize the seed queue of fuzzing by executing the initial seeds in the corpus
        for scenario in self.corpus:
            LOG.info(scenario.seed_path)
            mutator, res = self.run_instance(scenario)
            if res is not None:
                scenario.verified = True
                scenario.score = res
                self.population_add((scenario, mutator))
                self.hashes.add(scenario.get_hash())

        # the fuzzing loop
        while len(self.population) > 0:
            curr_scenario, curr_mutator = self.population_get()
            # mutation on curr scenario
            if self.strategy == "lawbreaker":
                tmp_scenario, tmp_mutator = self.population_get()
                new_scenario = curr_mutator.mutation2(tmp_mutator.encoded_testcase)
            else:
                try:
                    new_scenario = curr_mutator.mutation()
                except Exception as e:
                    LOG.error("Mutation Exception: {}".format(e))
                    continue
            new_scenario.store(self.workdir + "/queue/" + str(new_scenario.get_hash()))
            mutator, res = self.run_instance(new_scenario)
            if res is not None:
                if self.population_dup(res):
                    LOG.info("Similar seed: {}".format(new_scenario.get_hash()))
                    continue

                LOG.info("Original seed: {}".format(new_scenario.seed_path))
                LOG.info("Saved seed: {}".format(new_scenario.get_hash()))
                LOG.info("Queue size: {}".format(len(self.population)))
                new_scenario.verified = True
                new_scenario.score = res
                self.population_add((new_scenario, mutator))
                self.hashes.add(new_scenario.get_hash())
        return


@click.command()
@click.option(
    "-i",
    "--input",
    type=click.Path(file_okay=False, exists=True),
    required=True,
    help="The directory which contains the initial seeds(scenarios) for simulation-fuzzing.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False, exists=True),
    required=True,
    help="The output directory for fuzzer findings.",
)
@click.option(
    "-m",
    "--map",
    type=click.Path(dir_okay=False, exists=True),
    required=True,
    help="The xodr file which contains the map info.",
)
@click.option(
    "-s",
    "--strategy",
    type=click.Choice(["viohawk", "avfuzzer", "lawbreaker", "drivefuzz"]),
    default="viohawk",
    help="The strategy for fuzzing.",
)
@click.option(
    "-r",
    "--rule",
    type=str,
    required=True,
    help="The specific traffic rules for fuzzer.",
)
@timeout_decorator.timeout(10800, use_signals=False)
def fuzz(input, output, map, strategy, rule):
    """Execute Simulation Fuzzing"""
    LOG.info("Fuzzing Start.")
    LOG.info("Strategy: " + strategy)
    fuzzer = Fuzzer(input, output, map, strategy, rule)
    fuzzer.execute()
    LOG.info("Fuzzing End.")


if __name__ == "__main__":
    fuzz()
