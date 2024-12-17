output "alb_dns" {
  description = "DNS name of the private ALB"
  value       = aws_lb.private_lb.dns_name
}

output "ecs_cluster_name" {
  description = "ECS Cluster Name"
  value       = aws_ecs_cluster.ecs_cluster.name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL Endpoint"
  value       = aws_db_instance.postgres.endpoint
}
