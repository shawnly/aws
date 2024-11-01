#!/bin/bash

# Define the log file with date
log_date=$(date +'%Y-%m-%d')
log_file="client_output_${log_date}.log"

# Check if the WebSocket client is already running
if pgrep -f "node client.js" > /dev/null; then
  echo "WebSocket client is already running."
  exit 0
fi

# Start the WebSocket client and log output to a dated file
nohup node client.js > "$log_file" 2>&1 &

# Save the process ID (PID) to a file for easy reference
echo $! > client_pid.txt
echo "WebSocket client started with PID $! and logging to $log_file"
