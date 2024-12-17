#!/bin/bash
set -e

# Initialize Terraform
terraform init

# Plan Deployment
terraform plan -var-file=terraform.tfvars

# Apply Deployment
terraform apply -var-file=terraform.tfvars -auto-approve

# Show Outputs
terraform output
