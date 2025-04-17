#!/bin/bash
# Simple script to get security group outputs from a CloudFormation stack and export them

# Function to get specific output value by output key
get_stack_output() {
  local stack_name=$1
  local output_key=$2
  local profile=${3:-default}
  local region=${4:-us-east-1}
  
  aws cloudformation describe-stacks \
    --stack-name $stack_name \
    --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
    --output text \
    --profile $profile \
    --region $region
}

# Settings
STACK_NAME="multiple-sg-stack"  # Replace with your stack name
AWS_PROFILE=${AWS_PROFILE:-default}
AWS_REGION=${AWS_REGION:-us-east-1}

# Hardcoded output keys
OUTPUT_KEYS=("HttpsSGId" "WebSGId" "DatabaseSGId")

# Get and export each output value
for key in "${OUTPUT_KEYS[@]}"; do
  value=$(get_stack_output "$STACK_NAME" "$key" "$AWS_PROFILE" "$AWS_REGION")
  
  if [[ -n "$value" ]]; then
    # Export the variable
    export "${key}"="${value}"
    echo "Exported: ${key}=${value}"
  else
    echo "Warning: No value found for output key '${key}'"
  fi
done

# Return success
return 0