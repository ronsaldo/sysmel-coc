#!/bin/sh
set -ex

g++ -Wall -Wextra -std=c++17 -g -o smo2obj tools/smo2obj.cpp
