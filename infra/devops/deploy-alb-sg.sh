#!/bin/bash
# Script to deploy security groups stack, extract security group IDs, and deploy ALB stack

# Variables
SG_STACK_NAME="multiple-sg-stack"
ALB_STACK_NAME="alb-stack"
SG_TEMPLATE="multiple-sg-template.yaml"
ALB_TEMPLATE="alb-stack-template.yaml"
VPC_ID="vpc-xxxxxxxx"             # Replace with your VPC ID
REGION="us-east-1"                # Replace with your AWS region
SUBNET_IDS="subnet-xxxxx1,subnet-xxxxx2"  # Replace with your subnet IDs (at least 2 in different AZs)

# Step 1: Deploy the Security Groups stack
echo "Deploying Security Groups stack: $SG_STACK_NAME"
aws cloudformation deploy \
  --stack-name $SG_STACK_NAME \
  --template-file $SG_TEMPLATE \
  --parameter-overrides \
    VpcId=$VPC_ID \
  --region $REGION \
  --capabilities CAPABILITY_IAM

# Wait for stack creation to complete
echo "Waiting for Security Groups stack deployment to complete..."
aws cloudformation wait stack-create-complete --stack-name $SG_STACK_NAME --region $REGION 2>/dev/null || true
aws cloudformation wait stack-update-complete --stack-name $SG_STACK_NAME --region $REGION 2>/dev/null || true

# Step 2: Get Security Group IDs from stack outputs
echo "Retrieving Security Group IDs from stack outputs..."

# Function to get output value by output key
get_stack_output() {
  local stack_name=$1
  local output_key=$2
  
  aws cloudformation describe-stacks \
    --stack-name $stack_name \
    --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
    --output text \
    --region $REGION
}

# Get specific security group IDs by their output names
ALB_SG_ID=$(get_stack_output $SG_STACK_NAME "ALBSGId")
WEBSERVER_SG_ID=$(get_stack_output $SG_STACK_NAME "WebServerSGId")

echo "ALB Security Group ID: $ALB_SG_ID"
echo "Web Server Security Group ID: $WEBSERVER_SG_ID"

# Step 3: Deploy the ALB stack with the security group IDs
echo "Deploying ALB stack: $ALB_STACK_NAME"
aws cloudformation deploy \
  --stack-name $ALB_STACK_NAME \
  --template-file $ALB_TEMPLATE \
  --parameter-overrides \
    VpcId=$VPC_ID \
    Subnets=$SUBNET_IDS \
    ALBSecurityGroupId=$ALB_SG_ID \
    WebServerSecurityGroupId=$WEBSERVER_SG_ID \
  --region $REGION \
  --capabilities CAPABILITY_IAM

# Wait for ALB stack creation to complete
echo "Waiting for ALB stack deployment to complete..."
aws cloudformation wait stack-create-complete --stack-name $ALB_STACK_NAME --region $REGION 2>/dev/null || true
aws cloudformation wait stack-update-complete --stack-name $ALB_STACK_NAME --region $REGION 2>/dev/null || true

# Get the ALB DNS name
ALB_DNS=$(get_stack_output $ALB_STACK_NAME "LoadBalancerDNSName")
echo "ALB DNS Name: $ALB_DNS"

echo "Deployment complete!"