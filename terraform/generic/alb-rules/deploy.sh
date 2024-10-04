#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -m <DomainEC2Map> [-p <AWS profile>] [-c <config file>]"
    echo
    echo "Options:"
    echo "  -m    DomainEC2Map (required)"
    echo "  -p    AWS profile (optional, defaults to 'default')"
    echo "  -c    Configuration file for forwarding rules (optional, defaults to 'forwarding_rules.tfvars')"
    echo
    echo "Example:"
    echo "  $0 -m xsv-dev-01 -p myprofile -c custom_rules.tfvars"
    exit 1
}

# Initialize variables
DOMAIN_EC2_MAP=""
AWS_PROFILE="default"
CONFIG_FILE="forwarding_rules.tfvars"

# Parse command line options
while getopts ":m:p:c:" opt; do
    case $opt in
        m)
            DOMAIN_EC2_MAP="$OPTARG"
            ;;
        p)
            AWS_PROFILE="$OPTARG"
            ;;
        c)
            CONFIG_FILE="$OPTARG"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done

# Check if required parameters are provided
if [ -z "$DOMAIN_EC2_MAP" ]; then
    echo "Error: DomainEC2Map is required." >&2
    usage
fi

# Check if required commands exist
for cmd in terraform aws; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: $cmd is not installed or not in PATH." >&2
        exit 1
    fi
done

# Check if the config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file '$CONFIG_FILE' not found." >&2
    exit 1
fi

# Set AWS profile
export AWS_PROFILE="$AWS_PROFILE"

# Create or update terraform.tfvars
cat > terraform.tfvars << EOF
DomainEC2Map = "$DOMAIN_EC2_MAP"
event_id     = "deploy-$(date +%Y%m%d%H%M%S)"
EOF

# Run Terraform commands
echo "Initializing Terraform..."
terraform init

echo "Validating Terraform configuration..."
terraform validate

if [ $? -ne 0 ]; then
    echo "Error: Terraform validation failed." >&2
    exit 1
fi

echo "Planning Terraform changes..."
terraform plan -var-file="$CONFIG_FILE" -out=tfplan

echo "Applying Terraform changes..."
terraform apply tfplan

if [ $? -eq 0 ]; then
    echo "Deployment completed successfully."
    echo "ALB DNS Name: $(terraform output -raw alb_dns_name)"
else
    echo "Error: Terraform apply failed." >&2
    exit 1
fi