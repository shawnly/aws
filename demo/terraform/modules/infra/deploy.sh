#!/bin/bash
set -e

echo "Initializing Terraform..."
terraform init

echo "Validating Terraform..."
terraform validate

echo "Planning Terraform deployment..."
terraform plan -var-file="terraform.tfvars" -out=tfplan

echo "Applying Terraform configuration..."
terraform apply "tfplan"

echo "Deployment Complete!"
