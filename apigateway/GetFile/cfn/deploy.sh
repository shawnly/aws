#!/bin/bash

STACK_NAME=der-file-api
TEMPLATE_FILE=template.yaml
BUCKET_NAME=your-s3-bucket-name

aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --template-file $TEMPLATE_FILE \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides BucketName=$BUCKET_NAME
