# CodeBuild Project Deployment

This repository contains scripts to deploy an AWS CodeBuild project with GitHub Enterprise integration, including webhook setup for automated builds.

## Prerequisites

- AWS CLI installed and configured with appropriate credentials
- jq installed for JSON parsing
- GitHub Enterprise repository
- VPC and subnets configured in AWS
- GitHub Enterprise token stored in AWS Parameter Store

### Installing Dependencies

```bash
# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install jq awscli

# For CentOS/RHEL
sudo yum install jq awscli

# For macOS
brew install jq awscli
```

## Setup Instructions

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Copy and configure environment variables:
   ```bash
   cp env.sh.template env.sh
   chmod +x env.sh
   ```

3. Edit `env.sh` with your values:
   ```bash
   # GitHub Enterprise Repository URL
   export GITHUB_REPO_URL="https://github.enterprise.com/org/repo"

   # VPC Configuration
   export VPC_ID="vpc-xxxx"
   export SUBNET_IDS="subnet-xxxx,subnet-yyyy"

   # Stack Name (optional)
   export STACK_NAME="my-codebuild"
   ```

4. Make the deployment script executable:
   ```bash
   chmod +x deploy.sh
   ```

## Usage

### Basic Usage
```bash
./deploy.sh
```
This uses default values:
- Small compute size
- Event ID: 101
- Values from env.sh

### With Options
```bash
./deploy.sh --size medium --event 202
```

### Available Options
- `-s, --size`: Compute size (small/medium/large)
  - small: BUILD_GENERAL1_SMALL
  - medium: BUILD_GENERAL1_MEDIUM
  - large: BUILD_GENERAL1_LARGE
- `-e, --event`: Event ID for the build
- `-h, --help`: Show help message

## Files

- `deploy.sh`: Main deployment script
- `env.sh`: Environment configuration
- `template.yaml`: CloudFormation template
- `webhook_info.txt`: Generated webhook details (after deployment)

## Webhook Configuration

The script automatically:
1. Creates a webhook if it doesn't exist
2. Configures webhook triggers for:
   - Pull Request Created
   - Pull Request Updated
   - Pull Request Reopened
   - Push Events

Webhook details are saved to `webhook_info.txt`, including:
- Payload URL
- Secret
- Creation/modification date

## CloudFormation Stack

The deployment creates:
- CodeBuild Project
- IAM Role with required permissions
- Security Group for VPC access
- GitHub Enterprise webhook integration

## Troubleshooting

1. If deployment fails with VPC error:
   - Verify VPC_ID and SUBNET_IDS in env.sh
   - Ensure subnets have internet access (NAT Gateway/Internet Gateway)

2. If webhook creation fails:
   - Verify GitHub Enterprise token in Parameter Store
   - Check GitHub Enterprise repository URL format
   - Ensure AWS credentials have sufficient permissions

3. If build fails:
   - Check VPC networking (internet access)
   - Verify GitHub Enterprise connection
   - Review CodeBuild logs in AWS Console

## Security Notes

- Store sensitive values in env.sh
- Add env.sh to .gitignore
- Use AWS Parameter Store for GitHub token
- Review and customize IAM roles as needed

## Maintenance

- Update `env.sh` when changing environments
- Monitor webhook_info.txt for webhook details
- Regularly update compute size based on build requirements
- Review CloudWatch logs for build performance

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request