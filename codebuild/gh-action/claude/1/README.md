python create-codebuild-updated.py \
  --github-org "your-org-name" \
  --github-token "your-github-pat-token" \
  --aws-region "us-east-1" \
  --codebuild-project-name "your-project-name" \
  --vpc-id "vpc-12345" \
  --subnet-ids "subnet-12345,subnet-67890" \
  --security-group-id "sg-12345" \
  --service-role "arn:aws:iam::123456789012:role/YourCodeBuildRole" \
  --github-domain "github.com"