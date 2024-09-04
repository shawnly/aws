#!/bin/bash

# Ensure the script stops if any command fails
set -e

# Initialize Terraform
terraform init

# Prompt for AWS profile and VPC name
read -p "Enter your AWS profile name: " AWS_PROFILE
read -p "Enter the VPC name: " VPC_NAME
read -p "Enter the AWS region (default us-west-2): " AWS_REGION

# Set default AWS region if not provided
if [ -z "$AWS_REGION" ]; then
  AWS_REGION="us-west-2"
fi

# Run Terraform apply with input variables
terraform apply \
  -var="aws_profile=$AWS_PROFILE" \
  -var="vpc_name=$VPC_NAME" \
  -var="aws_region=$AWS_REGION" \
  -auto-approve
