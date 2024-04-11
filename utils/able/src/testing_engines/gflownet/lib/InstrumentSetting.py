import subprocess
import docker
from multiprocessing import Process

def reboot_svl():
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

def launch_apollo():
    pid = Process(target=reboot_svl)
    pid.start()
    return pid

def stop_apollo(pid):
    pid.terminate()
    if subprocess.call('cd ~/work/apollo;~/work/apollo/docker/scripts/dev_start.sh stop', shell=True):
        assert False, "Apollo container does not stop successfully."