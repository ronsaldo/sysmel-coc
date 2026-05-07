#!/bin/bash
set -ex

mkdir -p build/dist

gcc -Wall -Wextra -g -c -o build/dist/sysmel-runtime.o runtime/unityBuild.c -I. 
