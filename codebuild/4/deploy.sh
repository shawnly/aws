#!/bin/bash

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

size=$1
if [ -z "$size" ]; then
    echo "Usage: $0 <small|medium|large>"
    exit 1
fi

compute_type=$(get_compute_type "$size")
if [ $? -eq 0 ]; then
    aws cloudformation deploy \
        --template-file template.yaml \
        --stack-name my-codebuild \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
        ComputeType=$compute_type \
        VpcId=vpc-xxxx \
        SubnetIds=subnet-xxxx,subnet-yyyy
fi