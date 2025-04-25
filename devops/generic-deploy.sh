#!/bin/bash

# Initialize variables with default values
top_map=""
aws_credential="default"
service=""
docker_tag=""
git_ref=""

# Function to display usage
usage() {
  echo "Usage: $0 -m <product-project-domain-environment-ec2number> -s <service> [-c <aws_credential>] [-t <docker_tag>] [-g <git_ref>]"
  echo ""
  echo "Required parameters:"
  echo "  -m    Top Map in format product-project-domain-environment-ec2number (required)"
  echo "  -s    Service to deploy (required, use 'all' to deploy all services)"
  echo ""
  echo "Optional parameters:"
  echo "  -c    AWS credential profile (default: \"default\")"
  echo "  -t    Docker image tag (optional)"
  echo "  -g    Git commit ID or tag (optional)"
  echo ""
  echo "Example: $0 -m prod-uam-platform-dev-v01 -s myservice -c prod-profile -t v1.2.3 -g a1b2c3d4"
  echo "Example: $0 -m dev-etm-security-qa-v02 -s all -g main"
  exit 1
}

# Parse command line arguments
while getopts "m:c:s:t:g:" opt; do
  case $opt in
    m) top_map="$OPTARG" ;;
    c) aws_credential="$OPTARG" ;;
    s) service="$OPTARG" ;;
    t) docker_tag="$OPTARG" ;;
    g) git_ref="$OPTARG" ;;
    *) usage ;;
  esac
done

# Check if required parameters are provided
if [ -z "$top_map" ] || [ -z "$service" ]; then
  echo "Error: Missing required parameters."
  usage
fi

# Parse the top_map parameter
# Format: product-project-domain-environment-ec2number
IFS='-' read -r product project domain environment ec2number <<< "$top_map"

# Validate that all components of top_map were extracted
if [ -z "$product" ] || [ -z "$project" ] || [ -z "$domain" ] || [ -z "$environment" ] || [ -z "$ec2number" ]; then
  echo "Error: Invalid format for top_map parameter"
  echo "Expected format: product-project-domain-environment-ec2number"
  echo "Example: prod-uam-platform-dev-v01"
  usage
fi

# If no git_ref is provided, use the current git commit id
if [ -z "$git_ref" ]; then
  # This assumes the script is run in a git repository
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git_ref=$(git rev-parse HEAD)
    echo "No git reference specified, using current commit: $git_ref"
  else
    echo "Warning: Not in a git repository and no git reference specified."
    git_ref="latest"
    echo "Using default git reference: $git_ref"
  fi
fi

# If no docker_tag is provided, construct one from git_ref
if [ -z "$docker_tag" ]; then
  # Use short git commit as docker tag if it's a commit hash
  if [[ "$git_ref" =~ ^[0-9a-f]{40}$ ]]; then
    docker_tag="${git_ref:0:8}"
  else
    # Otherwise use the git_ref as is (e.g., branch or tag name)
    docker_tag="$git_ref"
  fi
  echo "No docker tag specified, using tag derived from git reference: $docker_tag"
fi

# Source the deployment function
if [ -f "./utils/deploy_service.sh" ]; then
  source ./utils/deploy_service.sh
else
  echo "Error: deploy_service.sh not found. Cannot proceed with deployment."
  exit 1
fi

# Display the configuration
echo "Deployment Configuration:"
echo "========================="
echo "Product: $product"
echo "Project: $project"
echo "Domain: $domain"
echo "Environment: $environment"
echo "EC2 Number: $ec2number"
echo "AWS Credential: $aws_credential"
echo "Service: $service"
echo "Docker Tag: $docker_tag"
echo "Git Reference: $git_ref"
echo "========================="

# Check if service is "all"
if [ "$service" = "all" ]; then
  echo "Deploying all services for $domain in $product $project..."
  
  # Source the get_service_list.sh script to get SERVICE_LIST
  if [ -f "./utils/get_service_lists.sh" ]; then
    source ./utils/get_service_lists.sh
    
    if [ -z "$SERVICE_LIST" ] || [ ${#SERVICE_LIST[@]} -eq 0 ]; then
      echo "Error: No services found in SERVICE_LIST."
      exit 1
    fi
    
    echo "Found ${#SERVICE_LIST[@]} services to deploy."
    
    # Track deployment status
    failed_services=()
    
    # Loop through SERVICE_LIST and deploy each service
    for current_service in "${SERVICE_LIST[@]}"; do
      echo ""
      echo "======================================"
      echo "Deploying service: $current_service"
      echo "======================================"
      
      # Call the deploy_service function
      # Updated to pass new parameters
      deploy_service "$current_service" "$domain" "$environment" "$ec2number" "$aws_credential" "$docker_tag" "$project" "$product" "$git_ref" &
      
      if [ $? -ne 0 ]; then
        echo "Service deployment failed: $current_service"
        failed_services+=("$current_service")
      fi
      
      echo "======================================"
    done
    
    echo ""
    if [ ${#failed_services[@]} -eq 0 ]; then
      echo "All services deployed successfully."
    else
      echo "The following services failed to deploy:"
      for failed_service in "${failed_services[@]}"; do
        echo "  - $failed_service"
      done
      exit 1
    fi
  else
    echo "Error: get_service_list.sh not found. Cannot deploy all services."
    exit 1
  fi
else
  # Deploy a single service
  echo "Deploying single service: $service for $domain in $product $project"
  
  # Call the deploy_service function with updated parameters
  deploy_service "$service" "$domain" "$environment" "$ec2number" "$aws_credential" "$docker_tag" "$project" "$product" "$git_ref"
  
  if [ $? -ne 0 ]; then
    echo "Service deployment failed: $service"
    exit 1
  else
    echo "Service deployed successfully: $service"
  fi
fi