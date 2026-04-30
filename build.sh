#!/bin/bash
set -ex

mkdir -p build/dist

g++ -Wall -Wextra -o build/dist/sysmelb bootstrap/UnityBuild.cpp -I. 