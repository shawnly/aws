#!/bin/bash

# Function to deploy a service
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
  
  echo "-- Deploying $service --"
  
  # Template selection based on service type
  local template_name
  if [[ "$service" == *-core ]]; then
    template_name="${service}-template.yaml"
    echo "Using core template: $template_name"
  else
    template_name="${service}.yaml"
    echo "Using regular template: $template_name"
  fi
  
  # Deploy with CloudFormation
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
  
  echo "-- Deployment completed for $service --"
}