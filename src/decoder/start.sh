#!/bin/bash
sleep 10
seq $(grep -c processor /proc/cpuinfo) | xargs -n 1 -P 100 nice /usr/bin/python3.6 /app/decoder.py
