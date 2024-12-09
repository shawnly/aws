# modules/rds/outputs.tf
output "db_instance_endpoint" {
  description = "The connection endpoint for the database"
  value       = aws_db_instance.postgresql.endpoint
}

output "db_instance_name" {
  description = "The name of the database"
  value       = aws_db_instance.postgresql.db_name
}

output "db_port" {
  description = "The port on which the database accepts connections"
  value       = aws_db_instance.postgresql.port
}

output "db_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "db_security_group_id" {
  description = "Security Group ID for the RDS instance"
  value       = aws_security_group.rds_sg.id
}