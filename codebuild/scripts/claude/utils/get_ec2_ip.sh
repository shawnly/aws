#!/bin/bash

# Function to display usage
usage() {
  echo "Usage: $0 -p <project_value> [-a <aws_profile>] [-r <region>]"
  echo ""
  echo "Required parameters:"
  echo "  -p    Project tag value"
  echo ""
  echo "Optional parameters:"
  echo "  -a    AWS profile (default: default)"
  echo "  -r    AWS region (default: us-east-1)"
  echo ""
  echo "Example: $0 -p my-project -a prod-profile -r us-west-2"
  echo ""
  echo "Output format: instance_id,private_ip (one entry per line)"
  exit 1
}

# Default values
project_value=""
aws_profile="default"
region="us-east-1"

# Parse command line arguments
while getopts "p:a:r:" opt; do
  case $opt in
    p) project_value="$OPTARG" ;;
    a) aws_profile="$OPTARG" ;;
    r) region="$OPTARG" ;;
    *) usage ;;
  esac
done

# Check if project value is provided
if [ -z "$project_value" ]; then
  echo "Error: Project tag value is required" >&2
  usage
fi

# Find EC2 instances with the specified Project tag
# Output only instance ID and private IP in a simple text format
instance_data=$(aws ec2 describe-instances \
  --profile "$aws_profile" \
  --region "$region" \
  --filters "Name=tag:Project,Values=$project_value" "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].[InstanceId,PrivateIpAddress]" \
  --output text)

if [ -z "$instance_data" ]; then
  echo "No instances found with Project=$project_value" >&2
  exit 1
else
  # Process the output to ensure one instance per line
  echo "$instance_data" | while read -r instance_id private_ip; do
    echo "$instance_id,$private_ip"
  done
fi