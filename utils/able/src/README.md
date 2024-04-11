# Prerequisites
1. A computer powerful enogh for running Apollo+LGSVL-2021.1. 
(Or two computers: one for Apollo, one for LGSVL)
2. rtamt (evaluating robustness degree of an STL formula, please refer to [the github page](https://github.com/nickovic/rtamt), downgrade antlr4 under 4.8)
3. python3
   ```bash
   sudo pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
   sudo pip3 install websockets pandas sklearn tqdm wsaccel shapely
   ```
4. Downgrade protobuf to version 3.19.

# Step by step

## Run Apollo with LGSVL
Please refer to [the detailed documentation](https://www.svlsimulator.com/docs/system-under-test/apollo-master-instructions/) for co-simulation of Apollo with LGSVL.
Set the LGSVL to API-Only mode.

Copy the content in `map/san_francisco` folder to Apollo: `apollo/modules/map/data/san_francisco/`
<!-- Then, Install the customized map map/original_map/base_map.bin to Apollo with the [guide](https://github.com/lgsvl/apollo-5.0/tree/simulator/modules/map/data). -->

## Setup our bridge.
1. Download and go to the root. Note that the source code should be downloaded and set up on the computer running Apollo.
	```bash
	git clone https://github.com/researcherzxd/ABLE.git
	cd ABLE-SourceCode
	```
2. Install Python API to support for LGSVL-2021.1.
	```bash
	cd ABLE-SourceCode/bridge/PythonAPImaster
	pip3 install --user -e .  
	##If "pip3 install --user -e ." fail, try the following command:
	python3 -m pip install -r requirements.txt --user .
	```

3. Connect our bridge to the LGSVL and Apollo:
	Go the bridge in the folder:/ABLE-SourceCode/bridge
	```bash
	cd /ABLE/bridge
	```
	Find file: [bridge.py](ABLE-SourceCode/bridge/bridge.py).
	There is class `Server` in [bridge.py](ABLE-SourceCode/bridge/bridge.py). 

	Modify the `SIMULATOR_HOST` and `SIMULATOR_PORT` of `Server` to your IP and port of LGSVL.
	Modify the `BRIDGE_HOST` and `BRIDGE_PORT` of `Server` to your IP and port of Apollo.
	
4. Test the parser:
	If the support for parser is properly installed, we can test it by running:
	```bash
	cd /ABLE
	python3 monitor.py
	```
	If there is no errors and warnings, the parser is correct.


## Run our bridge.
Open a terminal on the computer running Apollo.
```bash
cd /ABLE/bridge
python3 bridge.py
```
Keep it Running.


## Run the Generation Algorithm.
Open another terminal on the computer running Apollo.
```bash
cd /ABLE
python3 GFN_Fuzzing.py
```
If the brige is set properly, you will see the LGSVL and Apollo running. The results will be put into a folder that you set in path_config.py.


# Docker version
We have wrapped `ABLE` in  `Dockerfile`.

If you can run `Apollo` in docker, then you're already good to go.

The following steps are for setting up the docker image. You need to run only once.

0. update the path in `testing_engines/gflownet/path_config.py` to the following data: 
```
"test_result_direct": "/tmp/ABLE_output/data/apollo7/active+max/{}",
"debug_result_direct": "/tmp/ABLE_output/data/apollo7/debug/{}",
```

1. create an output folder at path `output_dir`, say: `/tmp/output_dir`

2. update the output directory path in the `docker_start.sh` file

3. open a terminal and `bash docker_build.sh`

The following steps are for running `ABLE`:

1. open a terminal and run: <br>`bash docker_start.sh`.<br>This will run a docker container with all the dependencies installed. 

2. within the docker container of step 1, run bridge: <br>`cd bridge && python bridge.py`

3. open another terminal and run: <br>`bash docker_enter.sh`. <br>This will enter the same docker container in step 1, run fuzzing using:<br> `cd testing_engines/gflownet && python GFN_Fuzzing.py`