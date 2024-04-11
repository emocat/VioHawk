# Implementation

This folder contains the source code for pylot, search algorithms and scripts.

(NOTE: this markdown file is made using [atom](https://atom.io); if you do not have a proper markdown viewer, you can use [this online viewer](https://dillinger.io))

## Directory Structure
- `runner`: the source code of search algorithms and pre-configured scripts to run them
- `pylot`: the code of our changes in pylot to make it compatible with our infrastructure
- `scripts`: the updated scripts for pylot to make it compatible with our infrastructure

## Usage
### For RQ1
Run the following command to run local search with any surrogate model:
```
cd runner
python3 run_LS_{surrogate_model}.py
```
and the results will be stored in output/temp folder.

To Run simulator for results of RQ1
```
cd runner
python3 runner_sim.py
```
The results will be stored in output/Res folder


### For RQ2/RQ3
Run the following command to run any search algorithm:
```
cd runner
python3 run_{Search_algorithm}.py
```
and the results will be stored in output/temp folder.
