#!/bin/bash

set +e

STDOUT_LOG="stdout.log"
STDERR_LOG="stderr.log"


# Start the GUI program in the background
$1 --github_token="$2" --github_user="$3" >"$STDOUT_LOG" 2>"$STDERR_LOG" &
PID=$!

# Wait for 60 seconds
sleep 60

# Check if the process is still running
if kill -0 $PID 2>/dev/null; then
    echo "Program is still running after 60 seconds. Terminating..."
    kill $PID
    wait $PID
    EXIT_CODE=$?
else
    echo "Program exited before 60 seconds."
    wait $PID
    EXIT_CODE=$?
fi

# Output the exit code
echo "Exit code: $EXIT_CODE"

if [ -f "$STDOUT_LOG" ]; then
    echo "=== Standard Output ==="
    cat "$STDOUT_LOG"
    rm "$STDOUT_LOG"
fi

if [ -f "$STDERR_LOG" ]; then
    echo "=== Standard Error ==="
    cat "$STDERR_LOG"
    rm "$STDERR_LOG"
fi

# Check if the program exited successfully
if [ $EXIT_CODE -eq 0 ]; then
    echo "Program executed successfully."
else
    echo "Program terminated with exit code $EXIT_CODE."
    exit $EXIT_CODE
fi
