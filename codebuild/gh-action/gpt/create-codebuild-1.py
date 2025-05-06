import boto3
import argparse
import json

def create_codebuild_project(args):
    client = boto3.client('codebuild')

    source = {
        'type': args.source_type,
        'location': f"https://github.com/{args.github_org}/{args.project_name}.git",
        'auth': {
            'type': 'OAUTH',
            'resource': args.github_token
        },
        'buildspec': 'buildspec.yml'
    }

    vpc_config = {
        'vpcId': args.vpc_id,
        'subnets': args.subnets.split(','),
        'securityGroupIds': args.security_group_ids.split(',')
    }

    environment = {
        'type': 'LINUX_CONTAINER',
        'image': 'aws/codebuild/standard:6.0',
        'computeType': args.compute_type,
        'privilegedMode': True,
        'environmentVariables': []
    }

    response = client.create_project(
        name=args.project_name,
        source=source,
        environment=environment,
        serviceRole=args.service_role,
        artifacts={'type': 'NO_ARTIFACTS'},
        vpcConfig=vpc_config,
        description='Project created by GitHub Action',
        timeoutInMinutes=60
    )

    print(json.dumps(response, indent=2, default=str))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-name', required=True)
    parser.add_argument('--source-type', required=True)
    parser.add_argument('--github-org', required=True)
    parser.add_argument('--github-token', required=True)
    parser.add_argument('--vpc-id', required=True)
    parser.add_argument('--subnets', required=True)  # comma-separated
    parser.add_argument('--security-group-ids', required=True)  # comma-separated
    parser.add_argument('--compute-type', required=True)
    parser.add_argument('--service-role', required=True)

    args = parser.parse_args()
    create_codebuild_project(args)
