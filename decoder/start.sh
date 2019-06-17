#!/bin/bash
sleep 10
seq $THREAD_NUM | xargs -n 1 -P 100 /usr/bin/python3.6 /app/decoder.py
