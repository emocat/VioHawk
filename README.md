# VioHawk

This project is a prototype for VioHawk. It aims to demonstrate the functionality and design of the tool from our paper **"VioHawk: Detecting Traffic Violations of Autonomous Driving Systems through Criticality-guided Simulation Testing"**.

## Structure

The project is structured as follows:

- `config/`: configuration files.
- `dataparser/`: scenario parser for the seed file.
- `logger/`: logging utils.
- `map/`: osm and processed map files.
- `mutator/`: code for calculating fitness score and applying mutation operators.
- `scripts/`: scripts for testing.
- `utils/`: helper module for map parsing, math calculation, and visualization.
- `fuzzer.py`: main entry point of the fuzzer.
- `run_vse.py`: simulation bridge for LGSVL and Apollo.

## Get Started

The VioHawk tools and experiments are tested under Python 3.7.16 with Ubuntu 18.04 and Nvidia RTX 2080 Ti.

First, LGSVL's python api should be installed: https://github.com/lgsvl/PythonAPI.

Then, install the requirements packages:

```
$ pip install -r requirements.txt
```

Besides, we provide a [docker environment](https://zenodo.org/records/12666547) to evaluate the **violation detection** and **scenario mutation** functionalities. It is worth noting that the docker is not equipped with GPU environment, so the simulation-based testing cannot be tested:

```
$ docker build -t viohawk:latest .
$ docker run -it viohawk:latest
```

## Functionality

### Simulation-based Fuzzing

Place the corpus seed in the `corpus/` directory. Specify the traffic rules that should be fuzzed (which is defined in mutator.py).

```
$ python3 fuzzer.py -i [corpus/] -o [out/] -m [map] -r [rule]
```

The fuzz results (intermediate and violated scenario seeds, traces) will be stored in the `out/` directory.

### Violation Detection

To detect whether a single scenario will violate a specific traffic rule:

```
$ python3 mutator.py detect -s [seed] -t [trace] -r [rule] -m [map]
```

### Scenario Mutation

To mutate a single scenario:

```
$ python3 mutator.py mutate -s [seed] -t [trace] -r [rule] -m [map] -o [mutated output file]
```

### Visualize

To visually display the hazardous areas and drivable areas of a given scenario:

```
$ python3 mutator.py visualize -s [seed] -t [trace] -r [rule] -m [map]
```

The generated GIF will be stored at `output/ZAM-mutation-1.gif`.

## How to Contribute

We value your contributions to improve VioHawk. Here’s how you can help:

- **Code Contributions:** Feel free to fork the repository, make your changes, and submit a pull request.
- **Issue Reporting:** If you encounter issues or have suggestions, please submit them as issues on GitHub.
