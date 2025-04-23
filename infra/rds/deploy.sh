#!/bin/bash
set -e

# Configuration variables
STACK_NAME="postgres-rds-stack"
REGION="us-east-1"
TEMPLATE_FILE="postgres-rds-template.yaml"
PARAMETERS_FILE="parameters.json"
S3_BUCKET=""  # Optional: for templates larger than 51,200 bytes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
# Deploy the CloudFormation stack using the parameters file
print_message "$GREEN" "Deploying CloudFormation stack: $STACK_NAME"
print_message "$YELLOW" "Using parameters from: $PARAMETERS_FILE"
print_message "$YELLOW" "This deployment may take 15-30 minutes to complete..."

aws cloudformation create-stack \
  --stack-name "$STACK_NAME" \
  $TEMPLATE_PARAM \
  --parameters file://$PARAMETERS_FILE \
  --capabilities CAPABILITY_IAM \
  --region "$REGION"

# Check if stack creation was initiated successfully
if [ $? -eq 0 ]; then
  print_message "$GREEN" "Stack creation initiated successfully!"
  print_message "$YELLOW" "Wait for stack creation to complete with: aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION"
  print_message "$YELLOW" "Monitor stack creation status with: aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION"
else
  print_message "$RED" "Failed to create stack. Please check the error message above."
  exit 1
fi