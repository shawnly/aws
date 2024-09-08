provider "aws" {
  profile = var.aws_profile  # AWS Profile from input
  region  = var.aws_region
}

# Get the VPC by name or tag (you can modify filters as needed)
data "aws_vpc" "selected_vpc" {
  filter {
    name   = "tag:Name"
    values = [var.vpc_name]  # Input parameter for the VPC name
  }
}

# Get subnets under the selected VPC
data "aws_subnets" "selected_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected_vpc.id]
  }
}

# Output the VPC CIDR block
data "aws_vpc" "vpc_cidr" {
  id = data.aws_vpc.selected_vpc.id
}
