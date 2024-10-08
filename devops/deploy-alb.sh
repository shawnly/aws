#!/bin/bash

# Function to display usage instructions
usage() {
  echo "Usage: $0 DomainEC2Map aws_profile"
  echo "Example: $0 project-1-dev-01 my-aws-profile"
  exit 1
}

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
  usage
fi

# Read parameters
DomainEC2Map=$1
AWS_PROFILE=$2

# Parse DomainEC2Map to extract project, environment, and ec2_id using IFS
IFS='-' read -r project environment ec2_id <<< "$DomainEC2Map"

# Define the project path
PROJECT_PATH="projects/$project/$environment"
MAIN_TF_TEMPLATE="main_template.tf"  # Path to the main.tf template

# Check if the directory exists, if not, create it and copy main.tf
if [ ! -d "$PROJECT_PATH" ]; then
  echo "Directory $PROJECT_PATH does not exist. Creating directory and copying main.tf..."
  
  # Create the directory structure
  mkdir -p "$PROJECT_PATH"
  
  # Copy the main.tf template to the new directory
  if [ -f "$MAIN_TF_TEMPLATE" ]; then
    cp "$MAIN_TF_TEMPLATE" "$PROJECT_PATH/main.tf"
    echo "main.tf copied to $PROJECT_PATH"
  else
    echo "Error: main.tf template not found at $MAIN_TF_TEMPLATE!"
    exit 1
  fi
fi

# Check if terraform.tfvars exists, if not, warn the user
if [ ! -f "$PROJECT_PATH/terraform.tfvars" ]; then
  echo "Warning: terraform.tfvars not found in $PROJECT_PATH. Please create and update terraform.tfvars before deploying."
  exit 1
fi

# Navigate to the appropriate directory
cd "$PROJECT_PATH" || exit

# Set the AWS profile as an environment variable for Terraform
export AWS_PROFILE=$AWS_PROFILE

# Initialize, plan, and apply Terraform
terraform init
terraform plan -var "aws_profile=$AWS_PROFILE" -var "domain_ec2_map=$DomainEC2Map"
terraform apply -var "aws_profile=$AWS_PROFILE" -var "domain_ec2_map=$DomainEC2Map" -auto-approve

echo "Deployment complete for $project-$environment with EC2 ID $ec2_id"
