#!/bin/bash

# Deployment script for S3 file retrieval with ALB Lambda in VPC (using NAT Gateway)

# Set variables (you can modify these)
STACK_NAME="s3-file-retrieval-stack"
S3_BUCKET_NAME="your-bucket-name"
LISTENER_ARN="arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-load-balancer/abcdef1234567890/1234567890123456"
PRIORITY=100
REGION="us-east-1"
VPC_ID="vpc-xxxxxxxxxxxxxxxxx"
SUBNET_IDS="subnet-xxxxxxxxxxxxxxxxx,subnet-yyyyyyyyyyyyyyyyy,subnet-zzzzzzzzzzzzzzzzz"  # Private subnets with NAT Gateway

# Check if all required parameters are provided
if [ -z "$S3_BUCKET_NAME" ] || [ -z "$LISTENER_ARN" ] || [ -z "$VPC_ID" ] || [ -z "$SUBNET_IDS" ]; then
    echo "Error: Please set S3_BUCKET_NAME, LISTENER_ARN, VPC_ID, and SUBNET_IDS variables"
    echo "Note: SUBNET_IDS should be private subnets with NAT Gateway access"
    exit 1
fi

# Check if CloudFormation template exists
if [ ! -f "template.yaml" ]; then
    echo "Error: CloudFormation template 'template.yaml' not found"
    exit 1
fi

# Deploy the CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME"
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        S3BucketName=$S3_BUCKET_NAME \
        ListenerArn=$LISTENER_ARN \
        Priority=$PRIORITY \
        VpcId=$VPC_ID \
        SubnetIds=$SUBNET_IDS \
    --capabilities CAPABILITY_IAM \
    --region $REGION

# Check deployment status
if [ $? -eq 0 ]; then
    echo "Deployment successful!"
    
    # Get stack outputs
    echo "Fetching stack outputs..."
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs' \
        --output table
else
    echo "Deployment failed!"
    exit 1
fi