#!/bin/bash

# Initialize variables with default values
domain_ec2_map=""
aws_credential="default"
service=""
tag=""

# Function to display usage
usage() {
  echo "Usage: $0 -m <domain-environment-ec2> -s <service> [-c <aws_credential>] [-t <tag>]"
  echo ""
  echo "Required parameters:"
  echo "  -m    Domain EC2 Map in format domain-environment-ec2 (required)"
  echo "  -s    Service to deploy (required, use 'all' to deploy all services)"
  echo ""
  echo "Optional parameters:"
  echo "  -c    AWS credential profile (default: \"default\")"
  echo "  -t    Tag to deploy (default: latest github commit id)"
  echo ""
  echo "Example: $0 -m uam-dev-v01 -s myservice -c prod-profile -t v1.2.3"
  echo "Example: $0 -m uam-dev-v01 -s all -c dev-profile"
  exit 1
}

# Parse command line arguments
while getopts "m:c:s:t:" opt; do
  case $opt in
    m) domain_ec2_map="$OPTARG" ;;
    c) aws_credential="$OPTARG" ;;
    s) service="$OPTARG" ;;
    t) tag="$OPTARG" ;;
    *) usage ;;
  esac
done

# Check if required parameters are provided
if [ -z "$domain_ec2_map" ] || [ -z "$service" ]; then
  echo "Error: Missing required parameters."
  usage
fi

# Parse the domain_ec2_map parameter
IFS='-' read -r domain environment ec2 <<< "$domain_ec2_map"

# Validate that all components of domain_ec2_map were extracted
if [ -z "$domain" ] || [ -z "$environment" ] || [ -z "$ec2" ]; then
  echo "Error: Invalid format for domain_ec2_map parameter"
  echo "Expected format: domain-environment-ec2"
  echo "Example: uam-dev-v01"
  usage
fi

# If tag is not provided, use latest github commit id
if [ -z "$tag" ]; then
  # This assumes the script is run in a git repository
  # If not in a git repo, this will fail and you may want to provide a fallback
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    tag=$(git rev-parse HEAD)
    echo "No tag specified, using latest commit: $tag"
  else
    echo "Warning: Not in a git repository and no tag specified."
    tag="latest"
    echo "Using default tag: $tag"
  fi
fi

# Display the configuration
echo "Deployment Configuration:"
echo "========================="
echo "Domain: $domain"
echo "Environment: $environment"
echo "EC2: $ec2"
echo "AWS Credential: $aws_credential"
echo "Service: $service"
echo "Tag: $tag"
echo "========================="

# Check if service is "all"
if [ "$service" = "all" ]; then
  echo "Deploying all services..."
  
  # Source the get_service_list.sh script to get SERVICE_LIST
  if [ -f "./get_service_list.sh" ]; then
    source ./get_service_list.sh
    
    if [ -z "$SERVICE_LIST" ] || [ ${#SERVICE_LIST[@]} -eq 0 ]; then
      echo "Error: No services found in SERVICE_LIST."
      exit 1
    fi
    
    echo "Found ${#SERVICE_LIST[@]} services to deploy."
    
    # Loop through SERVICE_LIST and deploy each service
    for current_service in "${SERVICE_LIST[@]}"; do
      echo ""
      echo "======================================"
      echo "Deploying service: $current_service"
      echo "======================================"
      
      # Add your deployment logic for each service here
      # For example:
      # deploy_service "$current_service" "$domain" "$environment" "$ec2" "$aws_credential" "$tag"
      
      # Example command:
      echo "Running deployment command for $current_service:"
      echo "aws --profile $aws_credential ec2 describe-instances --filters \"Name=tag:Name,Values=${domain}-${environment}-${ec2}\""
      echo "Deploying service '$current_service' with tag '$tag' to ${ec2} instance in ${environment} environment for ${domain} domain"
    done
    
    echo ""
    echo "All services deployed successfully."
  else
    echo "Error: get_service_list.sh not found. Cannot deploy all services."
    exit 1
  fi
else
  # Deploy a single service
  echo "Deploying single service: $service"
  
  # Add your deployment logic for a single service here
  # For example:
  # deploy_service "$service" "$domain" "$environment" "$ec2" "$aws_credential" "$tag"
  
  # Example command:
  echo "Running deployment command:"
  echo "aws --profile $aws_credential ec2 describe-instances --filters \"Name=tag:Name,Values=${domain}-${environment}-${ec2}\""
  echo "Deploying service '$service' with tag '$tag' to ${ec2} instance in ${environment} environment for ${domain} domain"
fi