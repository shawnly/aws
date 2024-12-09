aws cloudformation deploy \
  --template-file ecs-setup.yaml \
  --stack-name ECSClusterSetup \
  --parameter-overrides ClusterName=MyCluster KeyName=YourKeyPairName \
  --capabilities CAPABILITY_NAMED_IAM