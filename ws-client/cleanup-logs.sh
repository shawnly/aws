#!/bin/bash

# Configuration
LOG_DIR="/home/sport/prod/logs"
DAYS_TO_KEEP=30  # Adjust this value to keep logs for more or fewer days
LOG_PATTERN="ws-client-*.log"

# Ensure the log directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "Log directory $LOG_DIR does not exist!"
    exit 1
fi

# Delete old log files
echo "Cleaning up log files older than $DAYS_TO_KEEP days..."
find "$LOG_DIR" -name "$LOG_PATTERN" -type f -mtime +$DAYS_TO_KEEP -delete

# Count remaining log files
remaining_files=$(find "$LOG_DIR" -name "$LOG_PATTERN" -type f | wc -l)
echo "Cleanup complete. $remaining_files log files remaining."

# Optional: Print total size of remaining logs
total_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
echo "Current log directory size: $total_size"