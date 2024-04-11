#!/bin/bash

if [ -z "$CARLA_HOME" ]; then
    echo "Please set \$CARLA_HOME before running this script"
    exit 1
fi

if [ -z "$1" ]; then
    PORT=2000
else
    PORT=$1
fi

SDL_VIDEODRIVER=offscreen /home/erdos/workspace/Carla_Versions/CARLA_Shipping_0.9.10.1_noTrees/LinuxNoEditor/CarlaUE4.sh -opengl -windowed -ResX=800 -ResY=600 -carla-server -world-port=2000 -benchmark -fps=20 -quality-level=Epic
