#!/bin/bash

usage() {
    echo "Deploy CodeBuild project"
    echo "Usage: $0 [-s|--size <small|medium|large>] [-e|--event <event_id>]"
    echo
    echo "Options:"
    echo "  -s, --size    Size (small/medium/large), validates input size"
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

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -s|--size)
            size="${2,,}"  # Convert to lowercase
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

echo "Deploying with size: $size, event_id: ${event_id}"
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name my-codebuild \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
    ComputeSize=$size \
    VpcId=vpc-xxxx \
    SubnetIds=subnet-xxxx,subnet-yyyy \
    EventId=$event_id