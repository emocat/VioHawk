#!/usr/bin/env python3
#
# Copyright (c) 2020-2021 LG Electronics, Inc.
#
# This software contains code licensed as described in LICENSE.
#
# basic script for running a simple vse test
#

import os
import sys
import click

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import dataparser as _Parser
from run_vse import VSERunner


@click.command()
@click.option("-s", "--seed", type=click.Path(exists=True, dir_okay=False), required=True, help="scenario seed file")
@click.option("-c", "--conf", type=str, help="sensor configuration file")
@click.option("-t", "--time", type=int, default=30, help="time to run the scenario")
def run_vse_test_dev(seed: str, conf: str, time: int) -> None:
    scenario = _Parser.scenario_parser(seed)
    scenario.elements["time"][0].hour = 17

    vse_runner = VSERunner(scenario, _sensor_conf=conf)
    vse_runner.run(time)

    if len(vse_runner.collision_object_detail):
        ego = vse_runner.collision_object_detail[0]
        print(ego.position)


if __name__ == "__main__":
    run_vse_test_dev()
