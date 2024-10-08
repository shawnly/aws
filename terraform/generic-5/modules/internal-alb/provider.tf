provider "aws" {
  profile = var.aws_profile
  region  = "us-east-1" # Change this to your region
}

# Fetch the VPC and subnets based on the AWS profile
data "aws_vpc" "selected" {
  default = true
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }
}
