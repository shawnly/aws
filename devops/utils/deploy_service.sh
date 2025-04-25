#!/bin/bash

# Function to deploy a service
# Parameters:
#   $1: service name
#   $2: domain
#   $3: environment
#   $4: ec2number
#   $5: aws_credential
#   $6: docker_tag
#   $7: project
#   $8: product
#   $9: git_ref
deploy_service() {
  local service="$1"
  local domain="$2"
  local environment="$3"
  local ec2number="$4"
  local aws_credential="$5"
  local docker_tag="$6"
  local project="$7"
  local product="$8"
  local git_ref="$9"
  
  echo "Starting deployment for service: $service"
  
  # Check if the service ends with "-core"
  if [[ "$service" == *-core ]]; then
    echo "Core service detected: $service"
    local template_name="${service}-template.yaml"
    
    if [ ! -f "$template_name" ]; then
      echo "Error: Template file $template_name not found!"
      return 1
    fi
    
    echo "Deploying core service with CloudFormation template: $template_name"
    # CloudFormation deployment command for core services
    aws cloudformation deploy \
      --profile "$aws_credential" \
      --template-file "$template_name" \
      --stack-name "${service}-${environment}-stack" \
      --parameter-overrides \
        Domain="$domain" \
        Environment="$environment" \
        EC2Number="$ec2number" \
        Project="$project" \
        Product="$product" \
        DockerTag="$docker_tag" \
        GitRef="$git_ref" \
        ServiceName="$service" \
      --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
      --no-fail-on-empty-changeset
    
    local deploy_status=$?
    if [ $deploy_status -eq 0 ]; then
      echo "Core service deployment successful: $service"
    else
      echo "Error: Core service deployment failed: $service"
      return $deploy_status
    fi
  else
    echo "Regular service detected: $service"
    local template_name="${service}.yaml"
    
    if [ ! -f "$template_name" ]; then
      echo "Error: Template file $template_name not found!"
      return 1
    fi
    
    echo "Deploying regular service with CloudFormation template: $template_name"
    # CloudFormation deployment command for regular services
    aws cloudformation deploy \
      --profile "$aws_credential" \
      --template-file "$template_name" \
      --stack-name "${service}-${environment}-stack" \
      --parameter-overrides \
        Domain="$domain" \
        Environment="$environment" \
        EC2Number="$ec2number" \
        Project="$project" \
        Product="$product" \
        DockerTag="$docker_tag" \
        GitRef="$git_ref" \
        ServiceName="$service" \
      --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
      --no-fail-on-empty-changeset
    
    local deploy_status=$?
    if [ $deploy_status -eq 0 ]; then
      echo "Regular service deployment successful: $service"
    else
      echo "Error: Regular service deployment failed: $service"
      return $deploy_status
    fi
  fi
  
  return 0
}

# Check if this script is being sourced or executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  # Script is being run directly, show usage
  echo "This script is intended to be sourced by generic_deployment.sh"
  echo "It provides the deploy_service function for service deployment"
  echo ""
  echo "Usage:"
  echo "  In generic_deployment.sh: source ./deploy_service.sh"
  echo "  Then call: deploy_service \"\$service\" \"\$domain\" \"\$environment\" \"\$ec2number\" \"\$aws_credential\" \"\$docker_tag\" \"\$project\" \"\$product\" \"\$git_ref\""
fi