# Use data sources to retrieve VPC information dynamically

# Fetch the VPC ID based on a specific tag or name
data "aws_vpc" "selected_vpc" {
  tags = {
    Name = var.vpc_name  # Replace with the tag or name of your VPC
  }
}

# Get the CIDR block for the selected VPC
output "vpc_cidr_block" {
  value = data.aws_vpc.selected_vpc.cidr_block
}

# Fetch private subnets within the selected VPC
data "aws_subnets" "private_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected_vpc.id]
  }

  filter {
    name   = "tag:Type"
    values = ["private"]  # Replace with the tag key/value identifying private subnets
  }
}

# Output the private subnet IDs
output "private_subnet_ids" {
  value = data.aws_subnets.private_subnets.ids
}

in module reference 
module "security_groups" {
  source      = "../../modules/security_groups"
  project     = var.project
  environment = var.environment
  event_id    = var.event_id
  vpc_id      = data.aws_vpc.selected_vpc.id
  vpccidr     = data.aws_vpc.selected_vpc.cidr_block
}
