#!/bin/bash
if [ $# != 2 ]; then
    exit 1
fi
expected_output=$2
actual_output=$1

if diff -q "$actual_output" "$expected_output" > /dev/null; then
    exit 0
else
    exit 2
fi
