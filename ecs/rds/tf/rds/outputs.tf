output "rds_endpoint" {
  description = "RDS endpoint address"
  value       = aws_rds_instance.rds_instance.endpoint
}

output "rds_username" {
  description = "RDS master username"
  value       = var.master_username
}

output "rds_password_arn" {
  description = "Secrets Manager ARN for the RDS password"
  value       = aws_secretsmanager_secret.rds_password.arn
}
