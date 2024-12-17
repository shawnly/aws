output "nessus_security_group_id" {
  description = "NESSUS Security Group ID"
  value       = aws_security_group.nessus.id
}

output "https_security_group_id" {
  description = "HTTPS Security Group ID"
  value       = aws_security_group.https.id
}

output "alb_dns_name" {
  description = "Private ALB DNS Name"
  value       = aws_lb.private_lb.dns_name
}

output "ecs_cluster_name" {
  description = "ECS Cluster Name"
  value       = aws_ecs_cluster.ecs_cluster.name
}

output "ecs_instance_id" {
  description = "ECS Instance ID"
  value       = aws_instance.ecs_instance.id
}
