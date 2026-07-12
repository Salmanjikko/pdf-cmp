#!/bin/bash
count_errors=0
has_tests=0

files="../data/in_??_01.pdf"
for pdf_file in $files; do
    number=$(echo "$pdf_file" | grep -o "[0-9]*" | head -1)
    if [ -z "$number" ]; then
        break
    fi
    has_tests=1
    
    file_out="out_${number}.txt"
    if [ ! -f "../data/${file_out}" ]; then
        echo "TEST_${number}: FAILED (no expected output)"
        count_errors=$((count_errors + 1))
        continue
    fi
    
    ./test_case.sh "$number"
    error="$?"
    
    if [ "$error" -eq 0 ]; then
        echo "TEST_${number}: PASSED"
    else
        echo "TEST_${number}: FAILED"
        count_errors=$((count_errors + 1))
    fi
done

if [ "$count_errors" -eq 0 ]; then
    echo "All tests passed."
else
    echo "Failed $count_errors tests."
fi

if [ "$has_tests" -eq 0 ]; then
    echo "No tests found."
fi

exit "$count_errors"

