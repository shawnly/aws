# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# Security Groups
module "security_groups" {
  source = "./modules/security_groups"

  project     = var.project
  environment = var.environment
  event_id    = var.event_id
  vpc_id      = var.vpc_id
  vpc_cidr    = var.vpc_cidr
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project}-${var.environment}-ecs-${var.event_id}"
}

# ECS EC2 Instance
resource "aws_instance" "ecs_instance" {
  instance_type        = var.instance_type
  key_name             = var.ec2_key_name
  iam_instance_profile = var.ecs_instance_profile
  ami                  = "ami-075e0bc7e13861a3f"

  network_interface {
    network_interface_id = aws_network_interface.ecs_interface.id
    device_index         = 0
  }

  user_data = base64encode(templatefile("${path.module}/templates/ecs_user_data.tpl", {
    project     = var.project
    environment = var.environment
    event_id    = var.event_id
  }))

  tags = {
    Name           = "${var.project}-${var.environment}-${var.event_id}"
    DomainEC2Map   = var.domain_ec2_map
  }
}

resource "aws_network_interface" "ecs_interface" {
  subnet_id       = var.private_subnet_1
  security_groups = [module.security_groups.freddie_sg_id]
}

# Internal Application Load Balancer
resource "aws_lb" "private_lb" {
  name               = "${var.project}-${var.environment}-${var.ec2_number}"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [
    module.security_groups.https_sg_id, 
    module.security_groups.nessus_sg_id
  ]
  subnets = var.private_subnets

  enable_deletion_protection = true

  # Additional attributes from CloudFormation template
  idle_timeout = 4000

  tags = {
    Name = "${var.project}-${var.environment}-${var.ec2_number}"
  }
}

# Default Target Group
resource "aws_lb_target_group" "default" {
  name     = "Default-tg-${var.project}-${var.event_id}"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 6
    protocol            = "HTTP"
  }
}

# Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.private_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.default.arn
  }
}

# Health Check Listener Rule
resource "aws_lb_listener_rule" "health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "${var.project}-${var.environment}-alb-${var.event_id} http is health"
      status_code  = "200"
    }
  }

  condition {
    path_pattern {
      values = ["/alb-health"]
    }
  }
}