#!/bin/bash

# Variables
AWS_PROFILE="your_aws_profile" # Replace with your AWS profile name
TAG_KEY="DomainEC2Map"
TAG_VALUE="xsv-dev-01"

# Retrieve VPCs based on the tag key and value
vpc_id=$(aws ec2 describe-vpcs --profile $AWS_PROFILE \
  --query "Vpcs[?Tags[?Key=='$TAG_KEY' && Value=='$TAG_VALUE']].VpcId" \
  --output json | jq -r '.[0]')

# Check if the VPC ID was found
if [ -z "$vpc_id" ]; then
  echo "No VPC found with tag $TAG_KEY=$TAG_VALUE"
else
  echo "VPC ID: $vpc_id"
fi
