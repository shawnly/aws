#!/bin/bash

set -e

# Stack names
INFRA_STACK_NAME="infrastructure-stack"
APP_STACK_NAME="application-stack"

# CloudFormation templates
INFRA_TEMPLATE="infrastructure-stack.yaml"
APP_TEMPLATE="application-stack.yaml"

# Function to monitor deployment status
monitor_stack_status() {
  local stack_name=$1

  echo "Monitoring stack deployment: $stack_name"
  local stack_status="CREATE_IN_PROGRESS"

  while [[ "$stack_status" == "CREATE_IN_PROGRESS" || "$stack_status" == "UPDATE_IN_PROGRESS" ]]; do
    # Fetch the latest stack events
    aws cloudformation describe-stack-events \
      --stack-name "$stack_name" \
      --query "StackEvents[].[ResourceStatus, ResourceType, LogicalResourceId, Timestamp]" \
      --output table | head -n 15

    # Check the current status of the stack
    stack_status=$(aws cloudformation describe-stacks \
      --stack-name "$stack_name" \
      --query "Stacks[0].StackStatus" \
      --output text)

    # Wait for 10 seconds before the next status check
    sleep 10
    echo "Checking stack status..."
  done

  # Final stack status
  if [[ "$stack_status" == "CREATE_COMPLETE" || "$stack_status" == "UPDATE_COMPLETE" ]]; then
    echo "Stack deployment completed successfully: $stack_name"
  else
    echo "Error: Stack deployment failed with status $stack_status"
    exit 1
  fi
}

# Deploy infrastructure stack
echo "Deploying infrastructure stack..."
aws cloudformation deploy \
  --stack-name "$INFRA_STACK_NAME" \
  --template-file "$INFRA_TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM

# Monitor infrastructure stack deployment
monitor_stack_status "$INFRA_STACK_NAME"

# Get ListenerARN output
LISTENER_ARN=$(aws cloudformation describe-stacks \
  --stack-name "$INFRA_STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ListenerARN'].OutputValue" \
  --output text)

if [ -z "$LISTENER_ARN" ]; then
  echo "Error: ListenerARN output not found in infrastructure stack."
  exit 1
fi

echo "ListenerARN: $LISTENER_ARN"

# Deploy application stack
echo "Deploying application stack..."
aws cloudformation deploy \
  --stack-name "$APP_STACK_NAME" \
  --template-file "$APP_TEMPLATE" \
  --parameter-overrides ListenerARN="$LISTENER_ARN" \
  --capabilities CAPABILITY_NAMED_IAM

# Monitor application stack deployment
monitor_stack_status "$APP_STACK_NAME"
