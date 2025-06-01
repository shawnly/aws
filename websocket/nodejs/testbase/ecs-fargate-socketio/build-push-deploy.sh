#!/bin/bash
set -e

ECR_REPO="123456789012.dkr.ecr.us-west-2.amazonaws.com/socketio"
IMAGE_TAG="latest"
STACK_NAME="socketio-serviceA"
CF_TEMPLATE="cloudformation/ecs-fargate-socketio.yaml"

CLUSTER_NAME="your-ecs-cluster"
ALB_LISTENER_ARN="your-alb-listener-arn"
DOMAIN_NAME="https://your-domain.com"
SERVICE_PATH="serviceA"
MQ_HOST="activemq.example.com"
MQ_PORT="61613"
MQ_USER="admin"
MQ_PASSWORD="yourpassword"
MQ_QUEUE="websocket"

FULL_IMAGE_URI="${ECR_REPO}:${IMAGE_TAG}"

echo "🔧 Building Docker image..."
docker build -t $FULL_IMAGE_URI .

echo "📤 Pushing image to ECR..."
aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin $ECR_REPO
docker push $FULL_IMAGE_URI

echo "🚀 Deploying CloudFormation stack..."
aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --template-file $CF_TEMPLATE \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Environment=dev \
    ALBListenerArn=$ALB_LISTENER_ARN \
    ClusterName=$CLUSTER_NAME \
    ContainerImage=$FULL_IMAGE_URI \
    DomainName=$DOMAIN_NAME \
    MQHost=$MQ_HOST \
    MQPort=$MQ_PORT \
    MQUser=$MQ_USER \
    MQPassword=$MQ_PASSWORD \
    MQ_QUEUE=$MQ_QUEUE \
    ServicePath=$SERVICE_PATH
