import math
import os
import signal
from time import sleep

from testing_engines.gflownet.GFN_Fuzzing import covered_specs_7_31
from testing_engines.gflownet.generator.generative_model.main import generate_samples_with_gfn
from testing_engines.gflownet.generator.proxy.proxy_config import proxy_args
from testing_engines.gflownet.generator.proxy.train_proxy import train_proxy
from testing_engines.gflownet.path_config import path_args
import datetime
import subprocess
import docker
from multiprocessing import Process

def reboot_svl():
    if subprocess.call('cd ~/work/apollo;~/work/apollo/docker/scripts/dev_start.sh stop', shell=True):
        assert False, "Apollo container does not stop successfully."
    if subprocess.call('cd ~/work/apollo;./docker/scripts/dev_start.sh;./docker/scripts/dev_into.sh', shell=True):
        assert False, "Apollo container does not start successfully."
    client = docker.from_env()
    docker_ps_list = client.containers.list()
    docker_id = ""
    for container in docker_ps_list:
        if container.name == 'apollo_dev_xdzhang':
            docker_id = container.id
    if docker_id == "":
        assert False, "Apollo docker has not been starting well."
    cmd = "docker exec " + docker_id + " /bin/bash -c \"./scripts/bootstrap_lgsvl.sh\""
    if subprocess.call(cmd, shell=True):
        assert False, "Apollo docker has not been starting well."
    cmd = "docker exec " + docker_id + " /bin/bash -c \"./scripts/bridge.sh\""
    print("Apollo is beginning working...")
    if subprocess.call(cmd, stdout=subprocess.PIPE, shell=True):
        assert False, "Launching apollo-bridge is failed."


if __name__ == "__main__":
    # print(proxy_args)
    # train_proxy(proxy_args, "double_direction")
    # generate_samples_with_gfn("double_direction")
    # pid = Process(target=reboot_svl(), args=())
    # pid = Process(target=reboot_svl)
    # pid.start()
    # sleep(50)
    # pid.terminate()
    # if subprocess.call('cd ~/work/apollo;~/work/apollo/docker/scripts/dev_start.sh stop', shell=True):
    #     assert False, "Apollo container does not stop successfully."
    # pid = Process(target=reboot_svl)
    # pid.start()
    # sleep(2000)
    my_74 = [
        "eventually(((trafficLightAheadcolor==3)and(not(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))",
        "eventually(((rain>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually(((((trafficLightAheadcolor==2)and(stoplineAhead<=3.5))and(not(stoplineAhead<=0.5)))and(currentLanenumber>0))and(always[0,3](not(speed<0.5))))",
        "eventually((((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))",
        "eventually((((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(always[0,2](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(always[0,2](not(speed<0.5))))",
        "eventually(((fog>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually((fog>=0.5)and(not(fogLightOn==1)))",
        "eventually((fog>=0.5)and(not(warningflashOn==1)))",
        "eventually((((not(streetLightOn==1))and(Time>=20.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually((((not(streetLightOn==1))and(Time<=7.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually((rain>=0.5)and(not(speed<=30)))",
        "eventually((fog>=0.5)and(not(speed<=30)))",
        "eventually((isOverTaking==1)and(not(turnSignal==1)))",
        "eventually((isOverTaking==1)and((always[-1,2](not(hornOn==1)))and((not(highBeamOn==1))and(not(lowBeamOn==1)))))",
        "eventually((isOverTaking==1)and(always[0,10](not(turnSignal==2))))",
        "eventually((isOverTaking==1)and(always[0,10](not(isLaneChanging==1))))",
        "eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))",
        "eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time<=7.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))",
        "eventually((direction==2)and(not(turnSignal==2)))",
        "eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time>=20.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))",
        "eventually((isOverTaking==1)and(always[0,10]((isLaneChanging==1)and(not(NearestNPCAhead<=5.0)))))",
        "eventually(((isLaneChanging==1)and(currentLanenumber>=2))and(PriorityNPCAhead==1))",
        "eventually((direction==2)and(not(speed<=30)))",
        "eventually(((direction==2)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==2)and(stoplineAhead<=0.0))and(always[0,2](not(speed>0.5))))",
        "eventually(((((trafficLightAheadcolor==3)and(stoplineAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))",
        "eventually(((((trafficLightAheadcolor==3)and(junctionAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))",
        "eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(NPCAheadAhead<=0.5))"
    ]

    lb_74 = [
        "eventually((rain>=0.5)and(not(speed<=30)))",
        "eventually((fog>=0.5)and(not(speed<=30)))",
        "eventually(((rain>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually(((fog>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually((fog>=0.5)and(not(fogLightOn==1)))",
        "eventually((fog>=0.5)and(not(warningflashOn==1)))",
        "eventually((isOverTaking==1)and(not(turnSignal==1)))",
        "eventually((isOverTaking==1)and((always[-1,2](not(hornOn==1)))and((not(highBeamOn==1))and(not(lowBeamOn==1)))))",
        "eventually((isOverTaking==1)and(always[0,10](not(turnSignal==2))))",
        "eventually((isOverTaking==1)and(always[0,10](not(isLaneChanging==1))))",
        "eventually(((trafficLightAheadcolor==3)and(not(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))",
        "eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(NPCAheadAhead<=0.5))",
        "eventually((((not(streetLightOn==1))and(Time<=7.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually(((((trafficLightAheadcolor==2)and(stoplineAhead<=3.5))and(not(stoplineAhead<=0.5)))and(currentLanenumber>0))and(always[0,3](not(speed<0.5))))",
        "eventually((((not(streetLightOn==1))and(Time>=20.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually(((trafficLightAheadcolor==2)and(stoplineAhead<=0.0))and(always[0,2](not(speed>0.5))))",
        "eventually((((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))",
        "eventually((((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(always[0,2](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(always[0,2](not(speed<0.5))))",
        "eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time<=7.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))",
        "eventually(((((trafficLightAheadcolor==3)and(stoplineAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))",
        "eventually(((((trafficLightAheadcolor==3)and(junctionAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))",
        "eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time>=20.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))",
        "eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))",
        "eventually((isOverTaking==1)and(always[0,10]((isLaneChanging==1)and(not(NearestNPCAhead<=5.0)))))",
        "eventually(((isLaneChanging==1)and(currentLanenumber>=2))and(PriorityNPCAhead==1))",
        "eventually((((signalAhead==0)and(PriorityNPCAhead==1))and(junctionAhead<=1.0))and(always[0,2](not(speed<0.5))))"
    ]


    my_64 = ['eventually(((rain>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually(((fog>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually((fog>=0.5)and(not(fogLightOn==1)))', 'eventually((fog>=0.5)and(not(warningflashOn==1)))', 'eventually(((trafficLightAheadcolor==3)and(not(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))', 'eventually((((not(streetLightOn==1))and(Time<=7.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually((rain>=0.5)and(not(speed<=30)))', 'eventually((fog>=0.5)and(not(speed<=30)))', 'eventually((isOverTaking==1)and(not(turnSignal==1)))', 'eventually((isOverTaking==1)and((always[-1,2](not(hornOn==1)))and((not(highBeamOn==1))and(not(lowBeamOn==1)))))', 'eventually((isOverTaking==1)and(always[0,10](not(turnSignal==2))))', 'eventually((isOverTaking==1)and(always[0,10]((isLaneChanging==1)and(not(NearestNPCAhead<=5.0)))))', 'eventually((isOverTaking==1)and(always[0,10](not(isLaneChanging==1))))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(NPCAheadAhead<=0.5))', 'eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time<=7.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))', 'eventually(((trafficLightAheadcolor==2)and(stoplineAhead<=0.0))and(always[0,2](not(speed>0.5))))', 'eventually(((((trafficLightAheadcolor==3)and(stoplineAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))', 'eventually(((((trafficLightAheadcolor==3)and(junctionAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))', 'eventually((((not(streetLightOn==1))and(Time>=20.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))', 'eventually((((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))', 'eventually((((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))', 'eventually(((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(always[0,2](not(speed<0.5))))', 'eventually(((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(always[0,2](not(speed<0.5))))', 'eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time>=20.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))', 'eventually(((((trafficLightAheadcolor==2)and(stoplineAhead<=3.5))and(not(stoplineAhead<=0.5)))and(currentLanenumber>0))and(always[0,3](not(speed<0.5))))', 'eventually((direction==2)and(not(turnSignal==2)))', 'eventually(((isTrafficJam==1)and(NPCAheadspeed<0.5))and(always[0,2](not(speed<0.5))))']

    lb_64 = ['eventually((isOverTaking==1)and(not(turnSignal==1)))', 'eventually((isOverTaking==1)and((always[-1,2](not(hornOn==1)))and((not(highBeamOn==1))and(not(lowBeamOn==1)))))', 'eventually((isOverTaking==1)and(always[0,10](not(turnSignal==2))))', 'eventually((isOverTaking==1)and(always[0,10](not(isLaneChanging==1))))', 'eventually(((trafficLightAheadcolor==3)and(not(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))', 'eventually((((not(streetLightOn==1))and(Time<=7.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually(((rain>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually(((((trafficLightAheadcolor==2)and(stoplineAhead<=3.5))and(not(stoplineAhead<=0.5)))and(currentLanenumber>0))and(always[0,3](not(speed<0.5))))', 'eventually((rain>=0.5)and(not(speed<=30)))', 'eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time<=7.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))', 'eventually((((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))', 'eventually((((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))', 'eventually(((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(always[0,2](not(speed<0.5))))', 'eventually(((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(always[0,2](not(speed<0.5))))', 'eventually((fog>=0.5)and(not(speed<=30)))', 'eventually(((fog>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually((fog>=0.5)and(not(fogLightOn==1)))', 'eventually((fog>=0.5)and(not(warningflashOn==1)))', 'eventually((((not(streetLightOn==1))and(Time>=20.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(NPCAheadAhead<=0.5))', 'eventually(((((trafficLightAheadcolor==3)and(junctionAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))', 'eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time>=20.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))', 'eventually(((trafficLightAheadcolor==2)and(stoplineAhead<=0.0))and(always[0,2](not(speed>0.5))))', 'eventually(((((trafficLightAheadcolor==3)and(stoplineAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))', 'eventually((isOverTaking==1)and(always[0,10]((isLaneChanging==1)and(not(NearestNPCAhead<=5.0)))))', 'eventually((((signalAhead==0)and(PriorityNPCAhead==1))and(junctionAhead<=1.0))and(always[0,2](not(speed<0.5))))', 'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))']

    my_61 = ['eventually(((trafficLightAheadcolor==3)and(not(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))', 'eventually(((rain>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually(((fog>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually((fog>=0.5)and(not(fogLightOn==1)))', 'eventually((fog>=0.5)and(not(warningflashOn==1)))', 'eventually((rain>=0.5)and(not(speed<=30)))', 'eventually((isOverTaking==1)and(not(turnSignal==1)))', 'eventually((isOverTaking==1)and((always[-1,2](not(hornOn==1)))and((not(highBeamOn==1))and(not(lowBeamOn==1)))))', 'eventually((isOverTaking==1)and(always[0,10](not(turnSignal==2))))', 'eventually((isOverTaking==1)and(always[0,10](not(isLaneChanging==1))))', 'eventually((((not(streetLightOn==1))and(Time>=20.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually((fog>=0.5)and(not(speed<=30)))', 'eventually((((not(streetLightOn==1))and(Time<=7.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))', 'eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time<=7.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))', 'eventually(((trafficLightAheadcolor==2)and(stoplineAhead<=0.0))and(always[0,2](not(speed>0.5))))', 'eventually(((((trafficLightAheadcolor==2)and(stoplineAhead<=3.5))and(not(stoplineAhead<=0.5)))and(currentLanenumber>0))and(always[0,3](not(speed<0.5))))', 'eventually((((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))', 'eventually((((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))', 'eventually(((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(always[0,2](not(speed<0.5))))', 'eventually(((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(always[0,2](not(speed<0.5))))', 'eventually((isOverTaking==1)and(always[0,10]((isLaneChanging==1)and(not(NearestNPCAhead<=5.0)))))', 'eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time>=20.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))', 'eventually(((((trafficLightAheadcolor==3)and(stoplineAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))', 'eventually(((((trafficLightAheadcolor==3)and(junctionAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))']
    lb_61 = [
        "eventually((rain>=0.5)and(not(speed<=30)))",
        "eventually((fog>=0.5)and(not(speed<=30)))",
        "eventually(((trafficLightAheadcolor==3)and(not(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))",
        "eventually((((not(streetLightOn==1))and(Time<=7.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually(((rain>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually(((fog>=0.5)and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually((fog>=0.5)and(not(fogLightOn==1)))",
        "eventually((fog>=0.5)and(not(warningflashOn==1)))",
        "eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time<=7.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))",
        "eventually((((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))",
        "eventually((((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(not(direction==2)))and(always[0,3](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==1)and(stoplineAhead<=2.0))and(always[0,2](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==1)and(junctionAhead<=2.0))and(always[0,2](not(speed<0.5))))",
        "eventually((((not(streetLightOn==1))and(Time>=20.0))and(not(NPCAheadAhead<=10.0)))and(not(highBeamOn==1)))",
        "eventually(((((trafficLightAheadcolor==3)and(stoplineAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))",
        "eventually(((((trafficLightAheadcolor==3)and(junctionAhead<=2.0))and(not(PriorityNPCAhead==1)))and(not(PriorityPedsAhead==1)))and(always[0,2](not(speed>0.5))))",
        "eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time>=20.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))",
        "eventually((isOverTaking==1)and(not(turnSignal==1)))",
        "eventually((isOverTaking==1)and((always[-1,2](not(hornOn==1)))and((not(highBeamOn==1))and(not(lowBeamOn==1)))))",
        "eventually((isOverTaking==1)and(always[0,10](not(turnSignal==2))))",
        "eventually((isOverTaking==1)and(always[0,10](not(isLaneChanging==1))))",
        "eventually(((((trafficLightAheadcolor==2)and(stoplineAhead<=3.5))and(not(stoplineAhead<=0.5)))and(currentLanenumber>0))and(always[0,3](not(speed<0.5))))",
        "eventually(((trafficLightAheadcolor==2)and(stoplineAhead<=0.0))and(always[0,2](not(speed>0.5))))",
        "eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))"
    ]
    print(len(my_64), len(lb_64))
    # print(set(t_junction).union(set(my_tj2)) - set(lb_tj))
    # print(set(lb_tj) - set(t_junction).union(set(my_tj2)))
    print(set(my_64).difference(set(lb_64)))
    print(set(lb_64).difference(set(my_64)))
    print(set(lb_61).difference(set(my_61)))
    print(set(my_61).difference(set(lb_61)))



