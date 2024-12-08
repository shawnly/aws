aws cloudformation create-stack \
  --stack-name MyRDSStack \
  --template-body file://rds-template.yaml \
  --parameters ParameterKey=VpcId,ParameterValue=<YourVPCId> \
               ParameterKey=Tags,ParameterValue="Environment,Production" \
  --capabilities CAPABILITY_NAMED_IAM