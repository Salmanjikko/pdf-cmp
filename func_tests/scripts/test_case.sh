#!/bin/bash
num=$1
actual_output="actual_output.txt"

cd ../..

data_path="func_tests/data/"
pdf1="${data_path}in_${num}_01.pdf"
pdf2="${data_path}in_${num}_02.pdf"

if [ ! -f "$pdf1" ] || [ ! -f "$pdf2" ]; then
    echo "Error: Input files not found"
    exit 1
fi

source ~/pdf_env/bin/activate
python pdf_cmp.py "$pdf1" "$pdf2" > "./${actual_output}" 2>&1
error=$?

generated_pdf="${pdf1%.pdf}_${pdf2%.pdf}_cmp.pdf"
if [ -f "$generated_pdf" ]; then
    mv "$generated_pdf" "${data_path}out_${num}_cmp.pdf"
fi

cd ./func_tests/scripts

if [ "$error" -eq 0 ]; then
    if ./comparator.sh "../../${actual_output}" "../data/out_${num}.txt"; then
        exit 0
    else
        exit 1
    fi
else
    exit $error
fi