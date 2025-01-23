#!/bin/bash

set +x

usage() {
    echo "Deploy CodeBuild project with specified compute size and event ID"
    echo
    echo "Usage: $0 [-s|--size <small|medium|large>] [-e|--event <event_id>]"
    echo
    echo "Options:"
    echo "  -s, --size    Compute size (small/medium/large)"
    echo "                Default: small"
    echo "  -e, --event   Event ID for the build"
    echo "                Default: 101"
    echo
    echo "Examples:"
    echo "  $0                         # Uses defaults: small size, event 101"
    echo "  $0 -s medium              # Medium size, default event 101"
    echo "  $0 --size large --event 202 # Large size, event 202"
    echo "  $0 -e 303                  # Default small size, event 303"
    exit 1
}

get_compute_type() {
    case "$1" in
        small|SMALL)
            echo "BUILD_GENERAL1_SMALL"
            ;;
        medium|MEDIUM)
            echo "BUILD_GENERAL1_MEDIUM"
            ;;
        large|LARGE)
            echo "BUILD_GENERAL1_LARGE"
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
            size="$2"
            shift 2
            ;;
        -e|--event)
            event_id="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            ;;
    esac
done

compute_type=$(get_compute_type "$size")

echo "compute_type: $compute_type"
echo "event_id : $event_id"

# if [ $? -eq 0 ]; then
#     echo "Deploying with size: $size (${compute_type}), event_id: ${event_id}"
#     aws cloudformation deploy \
#         --template-file template.yaml \
#         --stack-name my-codebuild \
#         --capabilities CAPABILITY_IAM \
#         --parameter-overrides \
#         ComputeType=$compute_type \
#         VpcId=vpc-xxxx \
#         SubnetIds=subnet-xxxx,subnet-yyyy \
#         EventId=$event_id
# fi