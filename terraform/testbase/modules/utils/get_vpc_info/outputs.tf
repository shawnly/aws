output "vpc_id" {
  description = "The ID of the selected VPC"
  value       = data.aws_vpc.selected.id
}

output "vpc_cidr" {
  description = "The CIDR block of the selected VPC"
  value       = data.aws_vpc.selected.cidr_block
}

output "subnet_ids" {
  description = "A list of subnet IDs associated with the selected VPC"
  value       = data.aws_subnets.selected.ids
}
