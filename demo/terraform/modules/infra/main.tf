provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# NESSUS Security Group
resource "aws_security_group" "nessus_sg" {
  name        = "${var.project}-${var.environment}-nessus-sg-${var.event_id}"
  description = "Allow Nessus Scanner inbound traffic"
  vpc_id      = var.vpc_id

  ingress = [
    for cidr in ["128.102.4.216/32", "143.232.252.34/32", "128.102.195.216/32", "131.110.136.100/32"] : {
      from_port   = 0
      to_port     = 65535
      protocol    = "tcp"
      cidr_blocks = [cidr]
    }
  ]

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-nessus-sg-${var.event_id}"
  }
}

# HTTPS Security Group
resource "aws_security_group" "https_sg" {
  name        = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  description = "HTTPS access from allowed IPs"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = concat(
      ["156.68.0.0/16", "143.232.0.0/16", "129.168.0.0/16", "128.102.0.0/16"],
      [var.vpc_cidr]
    )
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  }
}

# Internal Application Load Balancer
resource "aws_lb" "private_lb" {
  name               = "${var.project}-${var.environment}-${var.ec2_number}"
  internal           = true
  load_balancer_type = "application"
  subnets            = var.private_subnets
  security_groups    = [aws_security_group.nessus_sg.id, aws_security_group.https_sg.id]

  tags = {
    Name = "${var.project}-${var.environment}-alb-${var.event_id}"
  }
}

# ALB Listener
resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.private_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "${var.project}-${var.environment}-alb-${var.event_id} http is health"
      status_code  = "200"
    }
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "${var.project}-${var.environment}-ecs-${var.event_id}"
  tags = {
    Name = "${var.project}-${var.environment}-ecs-${var.event_id}"
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "rds_subnet_group" {
  name        = "rds-subnet-group"
  description = "Subnet group for RDS"
  subnet_ids  = var.private_subnets

  tags = {
    Name = "rds-subnet-group"
  }
}

# PostgreSQL RDS Instance
resource "aws_db_instance" "postgres" {
  identifier              = "${var.project}-${var.environment}-${var.event_id}"
  engine                  = "postgres"
  engine_version          = "12.22"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_storage_size
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.rds_subnet_group.name
  publicly_accessible     = false
  deletion_protection     = true
  vpc_security_group_ids  = [aws_security_group.https_sg.id]

  tags = {
    Name = "${var.project}-${var.environment}-postgres-${var.event_id}"
  }
}
