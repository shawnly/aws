import boto3
import json
import requests
import argparse

def create_codebuild_organization_runner(github_org, github_token, aws_region, 
                                         codebuild_project_name, vpc_id, subnet_ids, 
                                         security_group_id, service_role, github_domain):
    client = boto3.client('codebuild', region_name=aws_region)
    try:
        # Step 1: Create CodeBuild Runner Project (Organization Level)
        response = client.create_project(
            name=codebuild_project_name,
            description='CodeBuild Runner for GitHub Enterprise Organization',
            source={
                'type': 'GITHUB_ENTERPRISE',
                'location': 'CODEBUILD_DEFAULT_WEBHOOK_SOURCE_LOCATION',
                'gitCloneDepth': 1,
                'reportBuildStatus': True,
                'gitSubmodulesConfig': {'fetchSubmodules': False}
            },
            artifacts={'type': 'NO_ARTIFACTS'},
            environment={
                'type': 'LINUX_CONTAINER',
                'image': 'aws/codebuild/amazonlinux2-x86_64-standard:5.0',
                'computeType': 'BUILD_GENERAL1_MEDIUM',
                'privilegedMode': False
            },
            vpcConfig={
                'vpcId': vpc_id,
                'subnets': subnet_ids.split(','),
                'securityGroupIds': [security_group_id]
            },
            serviceRole=service_role,
            timeoutInMinutes=60,
            queuedTimeoutInMinutes=480,
            logsConfig={'cloudWatchLogs': {'status': 'ENABLED'}},
            badgeEnabled=False,
        )
        print("✅ CodeBuild Runner Project Created Successfully!")
        print("🔹 Project ARN:", response['project']['arn'])
        
        # Step 2: Create Webhook with Organization-Level Runner
        webhook_response = client.create_webhook(
            projectName=codebuild_project_name,
            filterGroups=[[
                {'type': 'EVENT', 'pattern': 'WORKFLOW_JOB_QUEUED'}
            ]],
            manualCreation=True,  # Ensures AWS provides Payload URL instead of auto-creating
            scopeConfiguration={
                'name': github_org,  # GitHub Organization Name
                'domain': github_domain,
                'scope': 'GITHUB_ORGANIZATION'  # Sets it to Organization Level
            }
        )
        
        # Step 3: Extract Webhook Payload and Secret
        payload_url = webhook_response['webhook']['payloadUrl']
        secret_value = webhook_response['webhook']['secret']
        print("\n🚀 **GitHub Webhook Payload:**")
        print("🔹 Payload URL:", payload_url)
        print("🔹 Secret:", secret_value)
        
        # Step 4: Automatically Add Webhook to GitHub Organization
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        webhook_data = {
            "name": "web",
            "active": True,
            "events": ["workflow_job"],
            "config": {
                "url": payload_url,
                "content_type": "json",
                "secret": secret_value,
                "insecure_ssl": "0"
            }
        }
        github_api_url = f"https://api.github.com/orgs/{github_org}/hooks"
        github_response = requests.post(github_api_url, headers=headers, json=webhook_data)
        
        if github_response.status_code == 201:
            print("Webhook successfully created on GitHub Organization!")
        else:
            print(f"Failed to create GitHub Webhook. Response: {github_response.text}")
        
        return response, webhook_response
        
    except Exception as e:
        print(f"❌ Error creating CodeBuild project: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create AWS CodeBuild project with GitHub Enterprise integration')
    
    parser.add_argument('--github-org', required=True, help='GitHub Organization Name')
    parser.add_argument('--github-token', required=True, help='GitHub PAT with "admin:org_hook" scope')
    parser.add_argument('--aws-region', default='us-east-1', help='AWS Region (default: us-east-1)')
    parser.add_argument('--codebuild-project-name', required=True, help='CodeBuild Project Name')
    parser.add_argument('--vpc-id', required=True, help='VPC ID for CodeBuild')
    parser.add_argument('--subnet-ids', required=True, help='Comma-separated list of subnet IDs')
    parser.add_argument('--security-group-id', required=True, help='Security Group ID')
    parser.add_argument('--service-role', required=True, help='IAM Role ARN for CodeBuild')
    parser.add_argument('--github-domain', default='github.com', help='GitHub Enterprise domain (default: github.com)')
    
    args = parser.parse_args()
    
    create_codebuild_organization_runner(
        github_org=args.github_org,
        github_token=args.github_token,
        aws_region=args.aws_region,
        codebuild_project_name=args.codebuild_project_name,
        vpc_id=args.vpc_id,
        subnet_ids=args.subnet_ids,
        security_group_id=args.security_group_id,
        service_role=args.service_role,
        github_domain=args.github_domain
    )