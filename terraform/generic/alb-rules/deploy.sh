#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -m <DomainEC2Map> -p <AWS profile> -r <AWS region> -v <VPC name> -d <Domain name> [-c <config file>] [-n]"
    echo
    echo "Options:"
    echo "  -m    DomainEC2Map (required)"
    echo "  -p    AWS profile (required)"
    echo "  -r    AWS region (required)"
    echo "  -v    VPC name (required)"
    echo "  -d    Domain name for SSL certificate (required)"
    echo "  -c    Configuration file for forwarding rules (optional, defaults to 'forwarding_rules.tfvars')"
    echo "  -n    Do not create a new ALB, use existing one (optional)"
    echo
    echo "Example:"
    echo "  $0 -m xsv-dev-01 -p myprofile -r us-west-2 -v my-vpc -d example.com -c custom_rules.tfvars -n"
    exit 1
}

# Initialize variables
DOMAIN_EC2_MAP=""
AWS_PROFILE=""
AWS_REGION=""
VPC_NAME=""
DOMAIN_NAME=""
CONFIG_FILE="forwarding_rules.tfvars"
CREATE_ALB="true"

# Parse command line options
while getopts ":m:p:r:v:d:c:n" opt; do
    case $opt in
        m)
            DOMAIN_EC2_MAP="$OPTARG"
            ;;
        p)
            AWS_PROFILE="$OPTARG"
            ;;
        r)
            AWS_REGION="$OPTARG"
            ;;
        v)
            VPC_NAME="$OPTARG"
            ;;
        d)
            DOMAIN_NAME="$OPTARG"
            ;;
        c)
            CONFIG_FILE="$OPTARG"
            ;;
        n)
            CREATE_ALB="false"
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
if [ -z "$DOMAIN_EC2_MAP" ] || [ -z "$AWS_PROFILE" ] || [ -z "$AWS_REGION" ] || [ -z "$VPC_NAME" ] || [ -z "$DOMAIN_NAME" ]; then
    echo "Error: All required parameters must be provided." >&2
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

# Create or update terraform.tfvars
cat > terraform.tfvars << EOF
DomainEC2Map = "$DOMAIN_EC2_MAP"
aws_profile  = "$AWS_PROFILE"
aws_region   = "$AWS_REGION"
vpc_name     = "$VPC_NAME"
domain_name  = "$DOMAIN_NAME"
create_alb   = $CREATE_ALB
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
    echo "Listener ARN: $(terraform output -raw listener_arn)"
    echo "Target Group ARNs: $(terraform output -raw target_group_arns)"
else
    echo "Error: Terraform apply failed." >&2
    exit 1
fi