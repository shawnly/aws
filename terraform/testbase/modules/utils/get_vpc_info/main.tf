provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

data "aws_vpc" "selected" {
  id = var.vpc_id
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }
}

# Output the VPC CIDR block
data "aws_vpc" "vpc_cidr" {
  id = data.aws_vpc.selected.id
}
