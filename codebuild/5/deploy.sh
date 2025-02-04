#!/bin/bash

usage() {
    echo "Deploy CodeBuild project with GitHub Enterprise webhook"
    echo "Usage: $0 [-s|--size <small|medium|large>] [-e|--event <event_id>]"
    echo
    echo "Options:"
    echo "  -s, --size    Size (small/medium/large)"
    echo "  -e, --event   Event ID for the build (default: 101)"
}

validate_size() {
    case "$1" in
        small|SMALL|medium|MEDIUM|large|LARGE)
            return 0
            ;;
        *)
            echo "Invalid size. Use: small, medium, or large"
            exit 1
            ;;
    esac
}

validate_env() {
    if [ -z "$GITHUB_REPO_URL" ] || [ -z "$VPC_ID" ] || [ -z "$SUBNET_IDS" ]; then
        echo "Error: Required environment variables not set"
        echo "Please ensure env.sh sets GITHUB_REPO_URL, VPC_ID, and SUBNET_IDS"
        exit 1
    fi
}

# Default values
size="small"
event_id=101
# Get webhook output path from env.sh or use default
webhook_output=${WEBHOOK_OUTPUT_PATH:-"webhook_info.txt"}

# Source environment variables
if [ -f "env.sh" ]; then
    source env.sh
else
    echo "Error: env.sh not found"
    exit 1
fi

# Validate environment variables
validate_env

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -s|--size)
            size="${2,,}"
            validate_size "$size"
            shift 2
            ;;
        -e|--event)
            event_id="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done

# Deploy CloudFormation stack
echo "Deploying with:"
echo "  Repository: $GITHUB_REPO_URL"
echo "  VPC: $VPC_ID"
echo "  Subnets: $SUBNET_IDS"
echo "  Size: $size"
echo "  Event ID: $event_id"

aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name ${STACK_NAME:-my-codebuild} \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
    ComputeSize=$size \
    VpcId=$VPC_ID \
    SubnetIds=$SUBNET_IDS \
    EventId=$event_id \
    RepositoryUrl=$GITHUB_REPO_URL

# Get project name from stack outputs
project_name=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME:-my-codebuild} \
    --query 'Stacks[0].Outputs[?OutputKey==`ProjectName`].OutputValue' \
    --output text)

# Check if webhook already exists
webhook_exists=$(aws codebuild batch-get-projects --names $project_name \
    --query 'projects[0].webhook.url' --output text)

if [ "$webhook_exists" == "None" ]; then
    # Create webhook and save output
    webhook_info=$(aws codebuild create-webhook \
        --project-name $project_name \
        --filter-groups '[
          [
            {
              "type": "EVENT",
              "pattern": "PULL_REQUEST_CREATED, PULL_REQUEST_UPDATED, PULL_REQUEST_REOPENED, PUSH"
            }
          ]
        ]')
    
    # Check if webhook_output is a directory
    if [ -d "$webhook_output" ]; then
        webhook_output="${webhook_output}/webhook_info.txt"
    fi
    
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$webhook_output")"
    
    # Extract and save webhook details
    {
        echo "GitHub Webhook Information"
        echo "------------------------"
        echo "Project: $project_name"
        echo "Repository: $GITHUB_REPO_URL"
        echo "Payload URL: $(echo $webhook_info | jq -r '.webhook.payloadUrl')"
        echo "Secret: $(echo $webhook_info | jq -r '.webhook.secret')"
        echo "Created Date: $(date)"
    } > "$webhook_output"
    
    echo "Webhook created for project: $project_name"
    echo "Webhook details saved to: $webhook_output"
else
    echo "Webhook already exists for project: $project_name"
    
    # Get existing webhook info
    webhook_info=$(aws codebuild batch-get-projects --names $project_name)
    
    # Save existing webhook details
    echo "GitHub Webhook Information (Existing)" > $webhook_output
    echo "------------------------" >> $webhook_output
    echo "Project: $project_name" >> $webhook_output
    echo "Repository: $GITHUB_REPO_URL" >> $webhook_output
    echo "Payload URL: $(echo $webhook_info | jq -r '.projects[0].webhook.payloadUrl')" >> $webhook_output
    echo "Last Modified: $(date)" >> $webhook_output
    
    echo "Existing webhook details saved to: $webhook_output"
fi