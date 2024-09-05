output "vpc_id" {
  description = "The ID of the selected VPC."
  value       = data.aws_vpc.selected[0].id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the selected VPC."
  value       = data.aws_vpc.selected[0].cidr_block
}

output "subnet_ids" {
  description = "The IDs of the subnets within the selected VPC."
  value       = data.aws_subnets.selected.ids
}
