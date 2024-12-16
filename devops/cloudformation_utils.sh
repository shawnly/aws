#!/bin/bash

# Define color codes
RESET="\033[0m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
BLUE="\033[1;34m"

# Function to print colored messages
function print_status() {
  local color="$1"
  shift
  echo -e "${color}$@${RESET}"
}

# Function to monitor stack status with color output
function monitor_stack_status() {
  local stack_name=$1
  local stack_status="CREATE_IN_PROGRESS"

  print_status $BLUE "Monitoring stack deployment: $stack_name"

  while [[ "$stack_status" == "CREATE_IN_PROGRESS" || "$stack_status" == "UPDATE_IN_PROGRESS" ]]; do
    # Fetch the latest stack events
    events=$(aws cloudformation describe-stack-events \
      --stack-name "$stack_name" \
      --query "StackEvents[].[ResourceStatus, ResourceType, LogicalResourceId, Timestamp]" \
      --output text | head -n 10)

    clear
    print_status $BLUE "Recent events for stack: $stack_name"
    echo -e "${YELLOW}Status         | Type                        | Logical ID           | Timestamp${RESET}"
    echo "$events" | while read line; do
      echo "$line" | awk -v green="$GREEN" -v red="$RED" -v yellow="$YELLOW" -v reset="$RESET" '
      {
        if ($1 == "CREATE_COMPLETE" || $1 == "UPDATE_COMPLETE") {
          color = green;
        } else if ($1 == "CREATE_IN_PROGRESS" || $1 == "UPDATE_IN_PROGRESS") {
          color = yellow;
        } else {
          color = red;
        }
        printf "%s%s%s\n", color, $0, reset;
      }'
    done

    # Check the current status of the stack
    stack_status=$(aws cloudformation describe-stacks \
      --stack-name "$stack_name" \
      --query "Stacks[0].StackStatus" \
      --output text)

    sleep 5
  done

  # Final status message
  if [[ "$stack_status" == "CREATE_COMPLETE" || "$stack_status" == "UPDATE_COMPLETE" ]]; then
    print_status $GREEN "Stack deployment completed successfully: $stack_name"
  else
    print_status $RED "Error: Stack deployment failed with status $stack_status"
    exit 1
  fi
}
