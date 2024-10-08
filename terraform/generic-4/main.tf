# Variables for VPC, subnets, and DomainEC2Map
variable "aws_profile" {
  type        = string
  description = "AWS profile to use for finding vpc_id and subnets."
}

variable "domain_ec2_map" {
  type        = string
  description = "Combined parameter in the format project-environment-event_id."
}

variable "security_groups" {
  type        = list(string)
  description = "List of security groups for the ALB."
}

# Data sources to find VPC and subnets based on the profile
provider "aws" {
  profile = var.aws_profile
  region  = "us-east-1" # Adjust based on your needs
}

data "aws_vpc" "selected" {
  default = true
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }
}

# Parsing the DomainEC2Map to extract project, environment, and event_id
locals {
  domain      = split("-", var.domain_ec2_map)[0]
  environment = split("-", var.domain_ec2_map)[1]
  event_id    = split("-", var.domain_ec2_map)[2]
}

# Creating an internal ALB
resource "aws_lb" "internal_alb" {
  name               = "${local.domain}-${local.environment}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = var.security_groups
  subnets            = data.aws_subnets.selected.ids
}

# Default listener on port 80
resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.internal_alb.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "${local.domain}-${local.environment} is up"
      status_code  = "200"
    }
  }
}

# Rule for /alb-health path with fixed response
resource "aws_lb_listener_rule" "alb_health_rule" {
  listener_arn = aws_lb_listener.http_listener.arn
  priority     = 100

  action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "${local.domain}-${local.environment}-${local.event_id} is health"
      status_code  = "200"
    }
  }

  condition {
    path_pattern {
      values = ["/alb-health"]
    }
  }
}

output "alb_dns_name" {
  value = aws_lb.internal_alb.dns_name
}
