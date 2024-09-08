output "vpc_id" {
  value = data.aws_vpc.selected_vpc.id
  description = "The VPC ID of the selected VPC"
}

output "vpc_cidr" {
  value = data.aws_vpc.vpc_cidr.cidr_block
  description = "The CIDR block of the selected VPC"
}

output "subnet_ids" {
  value = data.aws_subnets.selected_subnets.ids
  description = "The IDs of the subnets in the selected VPC"
}
