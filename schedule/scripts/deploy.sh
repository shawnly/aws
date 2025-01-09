#!/bin/bash

# Help function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --ec2-start-time     EC2 start schedule (default: 'cron(0 8 ? * MON-FRI *)')"
    echo "  --ec2-stop-time      EC2 stop schedule (default: 'cron(0 18 ? * MON-FRI *)')"
    echo "  --rds-start-time     RDS start schedule (default: 'cron(0 8 ? * MON-FRI *)')"
    echo "  --rds-stop-time      RDS stop schedule (default: 'cron(0 18 ? * MON-FRI *)')"
    echo "  --tag-key            Resource tag key (default: 'scheduled')"
    echo "  --tag-value          Resource tag value (default: 'true')"
    echo "  --event-id           Event identifier (default: '101')"
    echo "  --stack-name         CloudFormation stack name (default: 'instance-scheduler')"
    echo "  --ec2-role-arn       ARN of EC2 Scheduler Lambda Role"
    echo "  --rds-role-arn       ARN of RDS Scheduler Lambda Role"
    echo "  -h, --help           Display this help message"
    exit 1
}

# Default values
EC2_START_TIME="cron(0 8 ? * MON-FRI *)"
EC2_STOP_TIME="cron(0 18 ? * MON-FRI *)"
RDS_START_TIME="cron(0 8 ? * MON-FRI *)"
RDS_STOP_TIME="cron(0 18 ? * MON-FRI *)"
TAG_KEY="scheduled"
TAG_VALUE="true"
EVENT_ID="101"
STACK_NAME="instance-scheduler"
EC2_ROLE_ARN=""
RDS_ROLE_ARN=""

# Parse named parameters
while [ $# -gt 0 ]; do
    case "$1" in
        --ec2-start-time)
            EC2_START_TIME="$2"
            shift 2
            ;;
        --ec2-stop-time)
            EC2_STOP_TIME="$2"
            shift 2
            ;;
        --rds-start-time)
            RDS_START_TIME="$2"
            shift 2
            ;;
        --rds-stop-time)
            RDS_STOP_TIME="$2"
            shift 2
            ;;
        --tag-key)
            TAG_KEY="$2"
            shift 2
            ;;
        --tag-value)
            TAG_VALUE="$2"
            shift 2
            ;;
        --event-id)
            EVENT_ID="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --ec2-role-arn)
            EC2_ROLE_ARN="$2"
            shift 2
            ;;
        --rds-role-arn)
            RDS_ROLE_ARN="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown parameter: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [ -z "$EC2_ROLE_ARN" ] || [ -z "$RDS_ROLE_ARN" ]; then
    echo "Error: EC2 and RDS role ARNs are required"
    echo "Please provide them using --ec2-role-arn and --rds-role-arn parameters"
    exit 1
fi

echo "Deploying with the following parameters:"
echo "EC2 Start Time: $EC2_START_TIME"
echo "EC2 Stop Time: $EC2_STOP_TIME"
echo "RDS Start Time: $RDS_START_TIME"
echo "RDS Stop Time: $RDS_STOP_TIME"
echo "Tag Key: $TAG_KEY"
echo "Tag Value: $TAG_VALUE"
echo "Event ID: $EVENT_ID"
echo "Stack Name: $STACK_NAME"
echo "EC2 Role ARN: $EC2_ROLE_ARN"
echo "RDS Role ARN: $RDS_ROLE_ARN"

# Confirm deployment
read -p "Do you want to proceed with the deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Deployment cancelled"
    exit 1
fi

# Create deployment packages
echo "Creating deployment packages..."
mkdir -p deployment/ec2 deployment/rds

# Copy Lambda function files
cp ec2_scheduler.py deployment/ec2/index.py
cp rds_scheduler.py deployment/rds/index.py

# Create EC2 Lambda zip
cd deployment/ec2
zip -r ../../ec2_function.zip .
cd ../..

# Create RDS Lambda zip
cd deployment/rds
zip -r ../../rds_function.zip .
cd ../..

# Deploy CloudFormation stack
echo "Deploying scheduler CloudFormation stack..."
aws cloudformation create-stack \
  --stack-name "$STACK_NAME" \
  --template-body file://scheduler-template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=EC2StartTime,ParameterValue="$EC2_START_TIME" \
    ParameterKey=EC2StopTime,ParameterValue="$EC2_STOP_TIME" \
    ParameterKey=RDSStartTime,ParameterValue="$RDS_START_TIME" \
    ParameterKey=RDSStopTime,ParameterValue="$RDS_STOP_TIME" \