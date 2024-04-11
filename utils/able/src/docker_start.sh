#!/usr/bin/env bash

output_dir="$(pwd)/../ABLE_output"
docker run --gpus all --network host -v "$output_dir:/tmp/ABLE_output" -v "$(pwd):/usr/src/app" --name able -it --rm able bash