#!/bin/bash
# scripts/deploy.sh
set -e

# Function to print colored output
print_step() {
    echo -e "\033[1;34m>>> $1\033[0m"
}

# Check if environment is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <environment>"
    echo "Environments: dev, staging, prod"
    exit 1
fi

ENVIRONMENT=$1
WORK_DIR="environments/${ENVIRONMENT}"

# Validate environment
if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Environment ${ENVIRONMENT} does not exist"
    exit 1
fi

# Change to environment directory
cd "$WORK_DIR"

# Terraform init
print_step "Initializing Terraform"
terraform init -upgrade

# Terraform validate
print_step "Validating Terraform configuration"
terraform validate

# Terraform plan
print_step "Planning Terraform changes"
terraform plan -out=tfplan

# Terraform apply
print_step "Applying Terraform changes"
terraform apply tfplan

# Clean up plan file
rm tfplan

print_step "Deployment completed successfully for ${ENVIRONMENT} environment"

#!/bin/bash
# scripts/destroy.sh
set -e

# Function to print colored output
print_step() {
    echo -e "\033[1;31m>>> $1\033[0m"
}

# Check if environment is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <environment>"
    echo "Environments: dev, staging, prod"
    exit 1
fi

ENVIRONMENT=$1
WORK_DIR="environments/${ENVIRONMENT}"

# Validate environment
if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Environment ${ENVIRONMENT} does not exist"
    exit 1
fi

# Change to environment directory
cd "$WORK_DIR"

# Confirm destruction
read -p "Are you sure you want to destroy the ${ENVIRONMENT} environment? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Destruction cancelled"
    exit 1
fi

# Terraform destroy
print_step "Destroying Terraform-managed infrastructure"
terraform destroy -auto-approve

print_step "Destruction completed successfully for ${ENVIRONMENT} environment"