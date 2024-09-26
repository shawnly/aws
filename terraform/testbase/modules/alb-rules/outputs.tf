output "target_group_arn" {
  description = "ARN of the created target group"
  value       = aws_lb_target_group.ec2_tg.arn
}
