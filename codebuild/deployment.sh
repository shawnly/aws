#!/bin/bash
# Deployment script for CodeBuild projects with GitHub Enterprise

# Default values
SIZE="small"
EVENT_ID="v101"
ORGANIZATION=""
AWS_REGION="us-east-1"
CLOUDFORMATION_TEMPLATE="codebuild-organization-template.yaml"
GITHUB_ENTERPRISE_URL="https://github.enterprise.example.com"
SECRET_NAME_GITHUB_TOKEN="github/personal-access-token"
SECRET_NAME_WEBHOOK="github/webhook-credentials"

# Function to display usage information
usage() {
  echo "Usage: $0 -o ORGANIZATION_NAME [-s SIZE] [-e EVENT_ID] [-r AWS_REGION] [-t TEMPLATE_PATH] [-g GITHUB_URL]"
  echo ""
  echo "Required:"
  echo "  -o ORGANIZATION_NAME   GitHub organization name"
  echo ""
  echo "Optional:"
  echo "  -s SIZE                Project size (small, medium, large) [default: small]"
  echo "  -e EVENT_ID            Event ID [default: v101]"
  echo "  -r AWS_REGION          AWS region [default: us-east-1]"
  echo "  -t TEMPLATE_PATH       Path to CloudFormation template [default: codebuild-organization-template.yaml]"
  echo "  -g GITHUB_URL          GitHub Enterprise URL [default: https://github.enterprise.example.com]"
  echo "  -h                     Show this help message"
  exit 1
}

# Parse command line arguments
while getopts "o:s:e:r:t:g:h" opt; do
  case $opt in
    o) ORGANIZATION="$OPTARG" ;;
    s) SIZE="$OPTARG" ;;
    e) EVENT_ID="$OPTARG" ;;
    r) AWS_REGION="$OPTARG" ;;
    t) CLOUDFORMATION_TEMPLATE="$OPTARG" ;;
    g) GITHUB_ENTERPRISE_URL="$OPTARG" ;;
    h) usage ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage ;;
  esac
done

# Validate required parameters
if [ -z "$ORGANIZATION" ]; then
  echo "ERROR: Organization name (-o) is required."
  usage
fi

# Validate and map size to CodeBuild compute type
case "$SIZE" in
  small|"") COMPUTE_TYPE="BUILD_GENERAL1_SMALL" ;;
  medium) COMPUTE_TYPE="BUILD_GENERAL1_MEDIUM" ;;
  large) COMPUTE_TYPE="BUILD_GENERAL1_LARGE" ;;
  *) echo "ERROR: Invalid size. Valid values are: small, medium, large"; exit 1 ;;
esac

# Print deployment information
echo "Deploying CodeBuild project with the following parameters:"
echo "  Organization: $ORGANIZATION"
echo "  Size: $SIZE (ComputeType: $COMPUTE_TYPE)"
echo "  Event ID: $EVENT_ID"
echo "  AWS Region: $AWS_REGION"
echo "  Template: $CLOUDFORMATION_TEMPLATE"
echo "  GitHub Enterprise URL: $GITHUB_ENTERPRISE_URL"
echo ""

# Function to retrieve a secret from AWS Secrets Manager
get_secret() {
  local secret_name=$1
  local json_key=$2
  
  SECRET_VALUE=$(aws secretsmanager get-secret-value \
    --region $AWS_REGION \
    --secret-id $secret_name \
    --query 'SecretString' \
    --output text)
  
  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to retrieve secret: $secret_name. Exiting."
    exit 1
  fi
  
  # If a specific JSON key is requested, extract it
  if [ -n "$json_key" ]; then
    echo $SECRET_VALUE | jq -r ".$json_key" 2>/dev/null
    if [ $? -ne 0 ]; then
      echo "ERROR: Failed to parse JSON secret or key not found: $json_key"
      exit 1
    fi
  else
    echo $SECRET_VALUE
  fi
}

# Create stack name based on organization and event ID
STACK_NAME="codebuild-${ORGANIZATION}-${EVENT_ID}"

# Function to deploy CloudFormation stack
deploy_stack() {
  echo "Retrieving GitHub token from Secrets Manager..."
  GITHUB_TOKEN=$(get_secret $SECRET_NAME_GITHUB_TOKEN "token")
  
  if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GitHub token not found in secret. Exiting."
    exit 1
  fi
  
  echo "Deploying CloudFormation stack: $STACK_NAME"
  
  # Deploy CloudFormation stack
  aws cloudformation deploy \
    --region $AWS_REGION \
    --template-file $CLOUDFORMATION_TEMPLATE \
    --stack-name $STACK_NAME \
    --parameter-overrides \
      GitHubEnterpriseServerUrl=$GITHUB_ENTERPRISE_URL \
      OrganizationName=$ORGANIZATION \
      DefaultRepositoryName="main-repo" \
      GitHubPersonalAccessToken=$GITHUB_TOKEN \
      ComputeType=$COMPUTE_TYPE \
      EventId=$EVENT_ID \
    --no-fail-on-empty-changeset
    
  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to deploy CloudFormation stack for $ORGANIZATION. Exiting."
    exit 1
  fi
  
  echo "Successfully deployed CloudFormation stack: $STACK_NAME"
}

# Function to configure webhook for the project
configure_webhook() {
  echo "Retrieving webhook credentials from AWS Secrets Manager..."
  
  # Get webhook URL and secret from Secrets Manager
  WEBHOOK_SECRET_JSON=$(get_secret $SECRET_NAME_WEBHOOK)
  WEBHOOK_URL=$(echo $WEBHOOK_SECRET_JSON | jq -r '.webhookUrl')
  WEBHOOK_SECRET=$(echo $WEBHOOK_SECRET_JSON | jq -r '.webhookSecret')
  
  # Validate that we got the values
  if [ -z "$WEBHOOK_URL" ] || [ -z "$WEBHOOK_SECRET" ]; then
    echo "ERROR: Failed to extract webhook URL or secret from the retrieved secret. Exiting."
    exit 1
  fi
  
  echo "Configuring webhook for project: $ORGANIZATION"
  
  # Determine the project name - this would typically be the organization name
  PROJECT_NAME=$ORGANIZATION
  
  # Create webhook for the project using the AWS CLI
  aws codebuild update-webhook \
    --region $AWS_REGION \
    --project-name $PROJECT_NAME \
    --filter-groups "[[{\"type\":\"EVENT\",\"pattern\":\"PUSH\"},{\"type\":\"BASE_REF\",\"pattern\":\"^refs/heads/main$\"}]]" \
    --url-hook-url "$WEBHOOK_URL" \
    --url-hook-secret "$WEBHOOK_SECRET"
    
  if [ $? -eq 0 ]; then
    echo "Successfully configured webhook for project: $PROJECT_NAME"
  else
    echo "ERROR: Failed to configure webhook for project: $PROJECT_NAME"
    exit 1
  fi
}

# Main execution
echo "Starting deployment process..."

# Deploy CloudFormation stack
deploy_stack

# Configure webhook for the project
configure_webhook

echo "Deployment complete! Stack '$STACK_NAME' and webhook have been configured."