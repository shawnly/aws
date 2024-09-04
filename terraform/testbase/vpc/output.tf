output "vpc_id" {
  description = "The ID of the selected VPC"
  value       = data.aws_vpc.selected_vpc.id
}

output "subnet_ids" {
  description = "The IDs of the selected subnets"
  value       = data.aws_subnets.selected_subnets.ids
}
