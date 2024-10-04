# modules/alb/main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

locals {
  parsed_map  = split("-", var.DomainEC2Map)
  domain      = local.parsed_map[0]
  environment = local.parsed_map[1]
  ec2         = local.parsed_map[2]
  alb_name    = "${local.domain}-${local.environment}-${var.event_id}-alb"
}

# Data source to check if ALB exists
data "aws_lb" "existing" {
  count = var.create_alb ? 0 : 1
  name  = local.alb_name
}

# Data source to check if HTTPS listener exists
data "aws_lb_listener" "https" {
  count             = var.create_alb ? 0 : 1
  load_balancer_arn = data.aws_lb.existing[0].arn
  port              = 443
}

# Create ALB if it doesn't exist
resource "aws_lb" "main" {
  count              = var.create_alb ? 1 : 0
  name               = local.alb_name
  internal           = true
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids

  tags = {
    Name        = local.alb_name
    Environment = local.environment
    Project     = local.domain
  }
}

# Create HTTPS listener if it doesn't exist
resource "aws_lb_listener" "https" {
  count             = var.create_alb ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.certificate_arn

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Default response"
      status_code  = "200"
    }
  }
}

# Create target groups
resource "aws_lb_target_group" "services" {
  for_each = var.forwarding_rules

  name     = "${local.domain}-${local.environment}-${each.key}"
  port     = each.value.target_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = each.value.health_path
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = each.value.response_code
  }
}

# Attach instances to target groups
resource "aws_lb_target_group_attachment" "services" {
  for_each = var.forwarding_rules

  count            = length(var.instance_ids)
  target_group_arn = aws_lb_target_group.services[each.key].arn
  target_id        = var.instance_ids[count.index]
  port             = each.value.target_port
}

# Create listener rules
resource "aws_lb_listener_rule" "services" {
  for_each = var.forwarding_rules

  listener_arn = var.create_alb ? aws_lb_listener.https[0].arn : data.aws_lb_listener.https[0].arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services[each.key].arn
  }

  condition {
    path_pattern {
      values = [each.value.path]
    }
  }
}

# modules/alb/variables.tf

variable "DomainEC2Map" {
  description = "Combined string of domain-environment-ec2"
  type        = string
}

variable "event_id" {
  description = "Event ID for the ALB"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs for the ALB"
  type        = list(string)
}

variable "forwarding_rules" {
  description = "Map of forwarding rules for services"
  type = map(object({
    path          = string
    priority      = number
    target_port   = number
    health_path   = string
    response_code = string
  }))
}

variable "vpc_id" {
  description = "The ID of the VPC to use"
  type        = string
}

variable "subnet_ids" {
  description = "The IDs of the subnets to use"
  type        = list(string)
}

variable "create_alb" {
  description = "Whether to create a new ALB or use an existing one"
  type        = bool
  default     = true
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate to use for HTTPS listener"
  type        = string
}

variable "instance_ids" {
  description = "List of EC2 instance IDs to attach to target groups"
  type        = list(string)
}

# modules/alb/outputs.tf

output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = var.create_alb ? aws_lb.main[0].dns_name : data.aws_lb.existing[0].dns_name
}

output "alb_arn" {
  description = "The ARN of the load balancer"
  value       = var.create_alb ? aws_lb.main[0].arn : data.aws_lb.existing[0].arn
}

output "target_group_arns" {
  description = "The ARNs of the target groups"
  value       = { for k, v in aws_lb_target_group.services : k => v.arn }
}

output "listener_arn" {
  description = "The ARN of the HTTPS listener"
  value       = var.create_alb ? aws_lb_listener.https[0].arn : data.aws_lb_listener.https[0].arn
}