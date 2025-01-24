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

# Default values
size="small"
event_id=101
stack_name="my-codebuild"

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
echo "Deploying with size: $size, event_id: ${event_id}"
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name $stack_name \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
    ComputeSize=$size \
    VpcId=vpc-xxxx \
    SubnetIds=subnet-xxxx,subnet-yyyy \
    EventId=$event_id

# Get project name from stack outputs
project_name=$(aws cloudformation describe-stacks \
    --stack-name $stack_name \
    --query 'Stacks[0].Outputs[?OutputKey==`ProjectName`].OutputValue' \
    --output text)

# Create webhook using AWS CLI
aws codebuild create-webhook \
    --project-name $project_name \
    --filter-groups "[[{\"type\":\"EVENT\",\"pattern\":\"WORKFLOW_JOB_QUEUE\"},{\"type\":\"HEAD_REF\",\"pattern\":\"refs/heads/main\"}]]"

echo "Webhook created for project: $project_name"