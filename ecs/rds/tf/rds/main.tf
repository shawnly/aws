resource "aws_security_group" "rds_security_group" {
  name_prefix = "${var.name_prefix}-rds-sg"
  description = "RDS security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Update to restrict access as needed
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_secretsmanager_secret" "rds_password" {
  name        = "${var.name_prefix}-rds-password"
  description = "Auto-generated password for RDS"

  generate_secret_string {
    secret_string_template = jsonencode({ username = var.master_username })
    generate_string_key    = "password"
    password_length        = 16
    exclude_characters     = "\"@/\\"
  }
}

resource "aws_rds_instance" "rds_instance" {
  allocated_storage       = var.allocated_storage
  engine                  = "postgres"
  engine_version          = var.engine_version
  instance_class          = var.instance_type
  username                = var.master_username
  password                = aws_secretsmanager_secret.rds_password.secret_string["password"]
  vpc_security_group_ids  = [aws_security_group.rds_security_group.id]
  db_subnet_group_name    = var.db_subnet_group_name
  availability_zone       = var.availability_zone
  tags                    = var.tags
}

output "rds_endpoint" {
  value = aws_rds_instance.rds_instance.endpoint
}

output "rds_username" {
  value = var.master_username
}

output "rds_password_arn" {
  value = aws_secretsmanager_secret.rds_password.arn
}
