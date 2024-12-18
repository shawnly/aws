# First, declare the subnet group
resource "aws_db_subnet_group" "main" {
  name        = "${var.project}-${var.environment}-${var.event_id}"
  subnet_ids  = var.private_subnets
  description = "Subnets available for the RDS DB Instance"
}

# Then reference it in the RDS instance
resource "aws_db_instance" "postgresql" {
  identifier           = "${var.project}-${var.environment}-${var.event_id}"
  engine              = "postgres"
  engine_version      = "12.22"
  instance_class      = var.db_instance_class
  allocated_storage   = var.db_storage_size
  storage_type        = "gp2"
  
  # Reference the subnet group
  db_subnet_group_name = aws_db_subnet_group.main.name  # This line should match exactly

  # ... other configurations
}
xxx  