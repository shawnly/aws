#!/bin/bash
STACK_NAME=create-codebuild-lambda
TEMPLATE=cloudformation-codebuild-lambda.yaml
REGION=us-west-2

echo "Deploying stack: $STACK_NAME"
aws cloudformation deploy \
  --template-file $TEMPLATE \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION
