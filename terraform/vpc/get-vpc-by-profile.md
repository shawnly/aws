Method 1: Using AWS Provider

    Configure AWS provider with profile:

Terraform

provider "aws" {
  region  = "us-west-2"
  profile = "your_profile_name"
}

    Use aws_vpc data source:

Terraform

data "aws_vpc" "example" {
  filter {
    name   = "tag:Name"
    values = ["your_vpc_name"]
  }
}

output "vpc_id" {
  value = data.aws_vpc.example.id
}

output "vpc_cidr" {
  value = data.aws_vpc.example.cidr_block
}

Replace "your_profile_name", "us-west-2", and "your_vpc_name" with your values.

Method 2: Using AWS CLI and Terraform External Data Source

    Create a file (get_vpc_info.sh) with:

Bash

#!/bin/bash
vpc_id=$(aws ec2 describe-vpcs --profile your_profile_name --query 'Vpcs[]|{VpcId: VpcId, CidrBlock: CidrBlock}' --output text)
echo "{\"vpc_id\":\"$vpc_id\"}"

    Make executable: chmod +x get_vpc_info.sh
    In Terraform:

Terraform

data "external" "vpc_info" {
  program = ["./get_vpc_info.sh"]
}

output "vpc_id" {
  value = jsondecode(data.external.vpc_info.result).vpc_id
}

output "vpc_cidr" {
  # Assuming CIDR is space-separated with VPC ID
  value = split(" ", jsondecode(data.external.vpc_info.result).vpc_id)[1]
}

Replace "your_profile_name" with your AWS profile name.
Method 3: Using Terraform AWS Data Sources with Filters
Terraform

data "aws_vpcs" "example" {
}

output "vpc_id" {
  value = data.aws_vpcs.example.ids[0]
}

output "vpc_cidr" {
  value = data.aws_vpcs.example.cidr_blocks[0]
}

aws ec2 describe-vpcs --profile <profile_name> --query 'Vpcs[]|{VpcId: VpcId, CidrBlock: CidrBlock}'


sam deploy \
  --template-file security-group-template.yaml \
  --stack-name your-stack-name \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides file://parameters.json \
  --profile your-profile

  parameters.json
  [
    {
        "ParameterKey": "VpcId",
        "ParameterValue": "your-vpc-id"
    },
    {
        "ParameterKey": "VpcCidr",
        "ParameterValue": "your-vpc-cidr"
    }
]

