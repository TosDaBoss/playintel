#!/bin/bash
# Monitor test progress

echo "Monitoring test progress..."
echo "Press Ctrl+C to stop monitoring"
echo

while true; do
    clear
    echo "==================================="
    echo "Test Progress Monitor"
    echo "Time: $(date '+%H:%M:%S')"
    echo "==================================="
    echo

    if [ -f "/Users/tosdaboss/playintel/test_output.log" ]; then
        tail -30 /Users/tosdaboss/playintel/test_output.log
    else
        echo "Waiting for tests to start..."
    fi

    echo
    echo "==================================="

    if [ -f "/Users/tosdaboss/playintel/test_results.json" ]; then
        echo "✅ Tests completed! Check test_results.json"
        break
    fi

    sleep 5
done
