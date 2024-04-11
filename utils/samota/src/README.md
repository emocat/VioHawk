# Replication Package for "Efficient Online Testing for DNN-Enabled Systems using Surrogate-Assisted and Many-Objective Optimization"

This repository contains the replication package of the paper "Efficient Online Testing for DNN-based Systems using Surrogate-Assisted and Many-Objective Optimization", ICSE 2022.

(NOTE: this markdown file is made using [atom](https://atom.io); if you do not have a proper markdown viewer, you can use [this online viewer](https://dillinger.io))


## Requirements

### Hardware
* NVIDIA GPU (>= 1080, RTX 2070+ is recommended)
* 16+ GB Memory
* 150+ GB Storage (SSD is recommended)

### Software
* Ubuntu 18.04
* python 3.6+
* nvidia-docker2 (see [pylot](https://github.com/erdos-project/pylot/tree/master/scripts) for more details)
* docker

### Python libararies
* pandas==1.1.5
* pymoo==0.4.2.2
* scikit-learn==0.24.2
* h5py==2.10.0
* scipy==1.4.1
* keras==2.4.0
* tensorflow==2.2.0
* numpy==1.21.5
* hdbscan==0.8.25

#### How to Install Python Libraries
Initialize python's virtual environment and install the required packages:
```shell script
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


## Directory Structure
- `implementation`: source code of search algorithms (SAMOTA and its alternatives), Pylot and automated evaluation scripts
- `data-analysis`: scripts to automatically process evaluation results data to generate figures
- `supporting-material`: supporting materials for safety requirements, constraints and possible values of test input attributes


## Installation

1. setup docker (Pylot) using the scripts from original website (https://github.com/erdos-project/pylot) or following the commands below

```bash
docker pull erdosproject/pylot:v0.3.2
nvidia-docker run -itd --name pylot -p 20022:22 erdosproject/pylot:v0.3.2 /bin/bash
```
2. create ssh-keys using following command and press enter twice when prompted
```bash
ssh-keygen
```

3. setup keys with Pylot by using the following commands
```bash
nvidia-docker cp ~/.ssh/id_rsa.pub pylot:/home/erdos/.ssh/authorized_keys
nvidia-docker exec -i -t pylot sudo chown erdos /home/erdos/.ssh/authorized_keys
nvidia-docker exec -i -t pylot sudo service ssh start
```
4. *download* the simulators from the following links and *extract* them to a folder name `Carla_Versions` (due to the figshare upload limit, the compressed file is divided into three)
* [Link_1](https://doi.org/10.6084/m9.figshare.16443321)
* [Link_2](https://doi.org/10.6084/m9.figshare.16443228)
* [Link_3](https://doi.org/10.6084/m9.figshare.16442883)

Note: if you are unable to execute these CARLA binaries on your machine, please follow the instructions [here](https://carla.readthedocs.io/en/0.9.10/build_linux/) to build CARLA on your local machine and edit it. You can create your own CARLA binaries by running the following command
```bash
make launch
```
The binaries for carla will appear in the build folder.

5. Run the following commands to setup Pylot with our changes
```bash
docker cp Carla_Versions pylot:/home/erdos/workspace/
ssh -p 20022 -X erdos@localhost
cd /home/erdos/workspace
mkdir results
cd pylot
rm -d -rf pylot
rm -d -rf scripts
```

```bash
logout
docker cp implementation/pylot pylot:/home/erdos/workspace/pylot/
docker cp implementation/scripts pylot:/home/erdos/workspace/pylot/
```
Note: in case error while running the simulator, log in to docker and change the permissions of scripts by using following commands
```bash
ssh -p 20022 -X erdos@localhost
cd /home/erdos/workspace/pylot/scripts
chmod +x run_simulator.sh
chmod +x run_simulator_without_b.sh
chmod +x run_simulator_without_t.sh
chmod +x run_simulator_without_t_b.sh
```

## Usage
run the search algorithm using the following code
```bash
cd implementation/runner
python3 run_{search_algorithm}.py
```
Note: Ignore `No such container:path: pylot:/home/erdos/workspace/results/finished.txt`.


log files will be generated in output folder
