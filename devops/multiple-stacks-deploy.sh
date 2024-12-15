#!/bin/bash

set -e

# Stack names
INFRA_STACK_NAME="infrastructure-stack"
APP_STACK_NAME="application-stack"

# CloudFormation templates
INFRA_TEMPLATE="infrastructure-stack.yaml"
APP_TEMPLATE="application-stack.yaml"

# Deploy infrastructure stack
echo "Deploying infrastructure stack..."
aws cloudformation deploy \
  --stack-name "$INFRA_STACK_NAME" \
  --template-file "$INFRA_TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for infrastructure stack to complete
echo "Waiting for infrastructure stack to complete..."
aws cloudformation wait stack-create-complete --stack-name "$INFRA_STACK_NAME"
echo "Infrastructure stack deployment completed."

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

# Wait for application stack to complete
echo "Waiting for application stack to complete..."
aws cloudformation wait stack-create-complete --stack-name "$APP_STACK_NAME"
echo "Application stack deployment completed."
