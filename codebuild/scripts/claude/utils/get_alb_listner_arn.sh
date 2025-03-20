#!/bin/bash

# Function to display usage
usage() {
  echo "Usage: $0 -d <domain> [-p <aws_profile>] [-r <region>]"
  echo ""
  echo "Required parameters:"
  echo "  -d    Domain name (value of the Domain_name tag)"
  echo ""
  echo "Optional parameters:"
  echo "  -p    AWS profile (default: default)"
  echo "  -r    AWS region (default: us-east-1)"
  echo ""
  echo "Example: $0 -d uam -p prod-profile -r us-west-2"
  exit 1
}

# Default values
domain=""
aws_profile="default"
region="us-east-1"

# Parse command line arguments
while getopts "d:p:r:" opt; do
  case $opt in
    d) domain="$OPTARG" ;;
    p) aws_profile="$OPTARG" ;;
    r) region="$OPTARG" ;;
    *) usage ;;
  esac
done

# Check if domain is provided
if [ -z "$domain" ]; then
  echo "Error: Domain name is required" >&2
  usage
fi

# Step 1: Find ALBs with the specified Domain_name tag
alb_arns=$(aws elbv2 describe-load-balancers \
  --profile "$aws_profile" \
  --region "$region" \
  --query "LoadBalancers[*].LoadBalancerArn" \
  --output text)

if [ -z "$alb_arns" ]; then
  echo "Error: No ALBs found in region $region" >&2
  exit 1
fi

# Step 2: Filter ALBs by the Domain_name tag
found_alb_arn=""
for alb_arn in $alb_arns; do
  # Get tags for the current ALB
  tags=$(aws elbv2 describe-tags \
    --profile "$aws_profile" \
    --region "$region" \
    --resource-arns "$alb_arn" \
    --query "TagDescriptions[0].Tags[?Key=='Domain_name' && Value=='$domain'].Value" \
    --output text)
  
  if [ -n "$tags" ]; then
    found_alb_arn="$alb_arn"
    break
  fi
done

if [ -z "$found_alb_arn" ]; then
  echo "Error: No ALBs found with Domain_name tag: $domain" >&2
  exit 1
fi

# Step 3: Find HTTPS listener for the identified ALB
https_listener=$(aws elbv2 describe-listeners \
  --profile "$aws_profile" \
  --region "$region" \
  --load-balancer-arn "$found_alb_arn" \
  --query "Listeners[?Protocol=='HTTPS'].ListenerArn" \
  --output text)

if [ -z "$https_listener" ]; then
  echo "Error: No HTTPS listener found for ALB with Domain_name: $domain" >&2
  exit 1
fi

# Output just the listener ARN, with no other text
echo "$https_listener"