import argparse
import boto3

parser = argparse.ArgumentParser()
parser.add_argument('--project-name', required=True)
parser.add_argument('--source-type', required=True)
parser.add_argument('--github-org', required=True)
parser.add_argument('--github-token', required=True)
parser.add_argument('--vpc-id', required=True)
parser.add_argument('--subnets', required=True)
parser.add_argument('--security-groups', required=True)
parser.add_argument('--compute-type', required=True)
parser.add_argument('--service-role', required=True)

args = parser.parse_args()

client = boto3.client('codebuild')

response = client.create_project(
    name=args.project_name,
    source={
        'type': args.source_type,
        'location': f'https://github.com/{args.github_org}/{args.project_name}.git',
        'gitCloneDepth': 1,
        'buildspec': 'buildspec.yml',
        'auth': {
            'type': 'OAUTH',
            'resource': args.github_token
        }
    },
    artifacts={'type': 'NO_ARTIFACTS'},
    environment={
        'type': 'LINUX_CONTAINER',
        'image': 'aws/codebuild/standard:6.0',
        'computeType': args.compute_type
    },
    serviceRole=args.service_role,
    vpcConfig={
        'vpcId': args.vpc_id,
        'subnets': args.subnets.split(','),
        'securityGroupIds': args.security_groups.split(',')
    },
    sourceVersion='main',
    badgeEnabled=True,
    webhook=True
)

# Extract webhook info
webhook_url = None
secret = None
try:
    webhook_info = client.batch_get_projects(names=[args.project_name])
    project_data = webhook_info['projects'][0]
    if 'webhook' in project_data:
        webhook_url = project_data['webhook'].get('url')
        secret = project_data['webhook'].get('secret')

        # Format safe filename using project name
        safe_project_name = args.project_name.replace("/", "-").replace(" ", "-")
        filename = f"codebuild-webhook-{safe_project_name}.md"

        # Save to Markdown
        with open(filename, "w") as f:
            f.write(f"# 🚀 AWS CodeBuild Webhook for `{args.project_name}`\n\n")
            f.write("Here are the details to manually configure your GitHub webhook:\n\n")
            f.write("## 🔗 Webhook URL\n")
            f.write(f"`{webhook_url}`\n\n")
            f.write("## 🔐 Webhook Secret\n")
            f.write(f"`{secret}`\n\n")
            f.write("> Paste this secret into GitHub → Settings → Webhooks → Secret.\n")

        print(f"✅ Webhook information saved to {filename}")
    else:
        print("ℹ️ No webhook info found.")
except Exception as e:
    print(f"⚠️ Could not retrieve webhook info: {e}")
