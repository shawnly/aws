output "target_group_arns" {
  description = "ARNs of the created target groups"
  value       = aws_lb_target_group.microservice_target_group[*].arn
}

output "listener_rule_ids" {
  description = "IDs of the created listener rules"
  value       = aws_lb_listener_rule.microservice_forwarding_rule[*].id
}
