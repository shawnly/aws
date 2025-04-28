aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name alb-der-api \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides BucketName=your-bucket