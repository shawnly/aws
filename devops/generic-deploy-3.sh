#!/bin/bash

# Initialize variables with default values
production=""
domain_ec2_map=""
aws_credential="default"
service=""
tag=""

# Function to display usage
usage() {
  echo "Usage: $0 -p <production> -m <domain-environment-ec2> -s <service> [-c <aws_credential>] [-t <tag>]"
  echo ""
  echo "Required parameters:"
  echo "  -p    Production flag (required)"
  echo "  -m    Domain EC2 Map in format domain-environment-ec2 (required)"
  echo "  -s    Service to deploy (required)"
  echo ""
  echo "Optional parameters:"
  echo "  -c    AWS credential profile (default: \"default\")"
  echo "  -t    Tag to deploy (default: latest github commit id)"
  echo ""
  echo "Example: $0 -p true -m uam-dev-v01 -s myservice -c prod-profile -t v1.2.3"
  exit 1
}

# Parse command line arguments
while getopts "p:m:c:s:t:" opt; do
  case $opt in
    p) production="$OPTARG" ;;
    m) domain_ec2_map="$OPTARG" ;;
    c) aws_credential="$OPTARG" ;;
    s) service="$OPTARG" ;;
    t) tag="$OPTARG" ;;
    *) usage ;;
  esac
done

# Check if required parameters are provided
if [ -z "$production" ] || [ -z "$domain_ec2_map" ] || [ -z "$service" ]; then
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
echo "Production: $production"
echo "Domain: $domain"
echo "Environment: $environment"
echo "EC2: $ec2"
echo "AWS Credential: $aws_credential"
echo "Service: $service"
echo "Tag: $tag"
echo "========================="

# Now you can use these variables in your deployment logic
# ...
# Deployment logic goes here
# ...

# Example usage of the parsed components:
echo ""
echo "Example deployment commands:"
echo "=============================="
echo "aws --profile $aws_credential ec2 describe-instances --filters \"Name=tag:Name,Values=${domain}-${environment}-${ec2}\""
echo "Deploy service '$service' with tag '$tag' to ${ec2} instance in ${environment} environment for ${domain} domain"
if [ "$production" = "true" ]; then
  echo "WARNING: This is a PRODUCTION deployment!"
fi