# CodeBuild GitHub Runner - Deployment Guide

This guide explains how to deploy the AWS Lambda function that creates a CodeBuild-based GitHub Actions self-hosted runner at the organization level.

## Overview

The solution consists of:

1. **Lambda Function** - Creates the CodeBuild project and GitHub webhook
2. **CloudFormation Template** - Deploys the Lambda function with appropriate IAM permissions
3. **GitHub Workflow** - Triggers the Lambda function to set up the runner

## Prerequisites

- AWS CLI configured with appropriate permissions
- GitHub Personal Access Token (PAT) with `admin:org_hook` scope
- AWS SSM Parameter Store set up for securely storing the GitHub token

## Deployment Steps

### 1. Store GitHub Token in AWS SSM Parameter Store

First, store your GitHub token securely in AWS SSM Parameter Store:

```bash
aws ssm put-parameter \
    --name GitHubTokenParameter \
    --value "your-github-token" \
    --type SecureString
```

### 2. Deploy CloudFormation Stack

```bash
aws cloudformation create-stack \
    --stack-name github-codebuild-runner \
    --template-body file://cloudformation-template.yaml \
    --parameters \
        ParameterKey=GitHubOrg,ParameterValue=your-github-org \
        ParameterKey=GitHubEnterpriseUrl,ParameterValue=developer.example.com \
        ParameterKey=VpcId,ParameterValue=vpc-xxxxxxxx \
        ParameterKey=SubnetIds,ParameterValue="subnet-xxxxxxxx\\,subnet-yyyyyyyy" \
        ParameterKey=SecurityGroupId,ParameterValue=sg-xxxxxxxx \
        ParameterKey=CodeBuildProjectName,ParameterValue=github-org-runner \
    --capabilities CAPABILITY_IAM
```

### 3. Configure GitHub Repository Secrets

Add the following secrets to your GitHub repository or organization:

- `VPC_ID`: Your VPC ID (e.g., `vpc-xxxxxxxx`)
- `SUBNET_IDS`: JSON array of subnet IDs (e.g., `["subnet-xxxxxxxx", "subnet-yyyyyyyy"]`)
- `SECURITY_GROUP_ID`: Your security group ID (e.g., `sg-xxxxxxxx`)
- `GITHUB_ENTERPRISE_DOMAIN`: Your GitHub Enterprise domain (e.g., `developer.example.com`)
- `CODEBUILD_SERVICE_ROLE_ARN`: ARN of the CodeBuild service role (from CloudFormation outputs)

### 4. Set up GitHub Actions Workflow

Create a `.github/workflows/setup-runner.yml` file in your repository with the content from the GitHub workflow example.

### 5. Trigger the Workflow

Trigger the workflow manually from the GitHub Actions tab of your repository. Provide the desired CodeBuild project name when prompted.

## How It Works

1. When the GitHub workflow is triggered:
   - It authenticates to AWS using OIDC
   - It retrieves the GitHub token from AWS Secrets Manager
   - It invokes the Lambda function with the required parameters

2. The Lambda function:
   - Creates a CodeBuild project configured to run as a GitHub Actions runner
   - Sets up a webhook between AWS CodeBuild and GitHub
   - Saves the webhook information to AWS Secrets Manager
   - Registers the webhook with your GitHub organization

3. Once the setup is complete:
   - GitHub workflow jobs with `runs-on: self-hosted` will be able to use the CodeBuild runner
   - The runner will be available at the organization level

## Troubleshooting

### Common Issues

1. **Lambda Execution Role Permissions**: Ensure the Lambda execution role has all the necessary permissions for CodeBuild, Secrets Manager, and EC2 networking.

2. **GitHub Token Scopes**: Verify your GitHub token has the `admin:org_hook` scope.

3. **Network Configuration**: Make sure the VPC, subnets, and security group allow the Lambda function to access the internet.

4. **CloudWatch Logs**: Check the Lambda function logs in CloudWatch for detailed error information.

### Getting Webhook Information

If you need to retrieve the webhook information after setup:

```bash
aws secretsmanager get-secret-value \
    --secret-id codebuild-github-runner-your-project-name
```

## Security Considerations

- The GitHub token is stored securely in AWS Secrets Manager
- The webhook secret is automatically generated and stored in AWS Secrets Manager
- The Lambda function and CodeBuild project run in your VPC for network isolation
- IAM roles follow the principle of least privilege

## Cleanup

To remove all resources:

```bash
aws cloudformation delete-stack \
    --stack-name github-codebuild-runner
```

This will delete the Lambda function, IAM roles, and Secrets Manager resources. You'll need to manually delete the webhook from your GitHub organization.

{
  "github_org": "your-github-org",
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "aws_region": "us-east-1",
  "codebuild_project_name": "github-org-runner",
  "vpc_id": "vpc-0123456789abcdef0",
  "subnet_ids": ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"],
  "security_group_id": "sg-0123456789abcdef0",
  "github_enterprise_domain": "developer.example.com",
  "service_role_arn": "arn:aws:iam::123456789012:role/codebuild-github-runner-service-role"
}