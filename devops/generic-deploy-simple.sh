#!/bin/bash

# Initialize variables with default values
top_map=""
aws_credential="default"
service=""
docker_tag=""
git_ref=""

# Parse command line arguments
while getopts "m:c:s:t:g:" opt; do
  case $opt in
    m) top_map="$OPTARG" ;;
    c) aws_credential="$OPTARG" ;;
    s) service="$OPTARG" ;;
    t) docker_tag="$OPTARG" ;;
    g) git_ref="$OPTARG" ;;
    *) echo "Usage: $0 -m <product-project-domain-environment-ec2number> -s <service> [-c <aws_credential>] [-t <docker_tag>] [-g <git_ref>]"; exit 1 ;;
  esac
done

# Check required parameters
if [ -z "$top_map" ] || [ -z "$service" ]; then
  echo "Error: Missing required parameters (-m and -s are required)"
  exit 1
fi

# Parse the top_map parameter
IFS='-' read -r product project domain environment ec2number <<< "$top_map"

# If no git_ref, use current git commit
[ -z "$git_ref" ] && git_ref=$(git rev-parse HEAD 2>/dev/null || echo "latest")

# If no docker_tag, derive from git_ref
[ -z "$docker_tag" ] && docker_tag="${git_ref:0:8}"

# Source the deployment function
source ./deploy_service_simple.sh

# Display configuration
echo "Deploying with:"
echo "Product: $product, Project: $project, Domain: $domain"
echo "Environment: $environment, EC2: $ec2number"
echo "Service: $service, Docker Tag: $docker_tag, Git Ref: $git_ref"

# Handle deployment
if [ "$service" = "all" ]; then
  echo "Deploying all services..."
  source ./get_service_list.sh
  for current_service in "${SERVICE_LIST[@]}"; do
    echo "Deploying service: $current_service"
    deploy_service "$current_service" "$domain" "$environment" "$ec2number" "$aws_credential" "$docker_tag" "$project" "$product" "$git_ref"
  done
else
  echo "Deploying single service: $service"
  deploy_service "$service" "$domain" "$environment" "$ec2number" "$aws_credential" "$docker_tag" "$project" "$product" "$git_ref"
fi