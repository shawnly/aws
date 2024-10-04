# main.tf

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
}

data "aws_vpc" "selected" {
  default = false
  state   = "available"

  tags = {
    Name = "${local.domain}-${local.environment}"
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }

  tags = {
    Tier = "Private"
  }
}

data "aws_acm_certificate" "selected" {
  tags = {
    DomainEC2Map = var.DomainEC2Map
  }
  most_recent = true
}

data "aws_instances" "selected" {
  filter {
    name   = "tag:DomainEC2Map"
    values = [var.DomainEC2Map]
  }
}

resource "aws_lb" "main" {
  name               = "${local.domain}-${local.environment}-${var.event_id}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = data.aws_subnets.private.ids

  tags = {
    Name        = "${local.domain}-${local.environment}-${var.event_id}-alb"
    Environment = local.environment
    Project     = local.domain
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = data.aws_acm_certificate.selected.arn

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Default response"
      status_code  = "200"
    }
  }
}

resource "aws_lb_target_group" "services" {
  for_each = var.forwarding_rules

  name     = "${local.domain}-${local.environment}-${each.key}"
  port     = each.value.target_port
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.selected.id

  health_check {
    path                = each.value.health_path
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = each.value.response_code
  }
}

resource "aws_lb_target_group_attachment" "services" {
  for_each = var.forwarding_rules

  count            = length(data.aws_instances.selected.ids)
  target_group_arn = aws_lb_target_group.services[each.key].arn
  target_id        = data.aws_instances.selected.ids[count.index]
  port             = each.value.target_port
}

resource "aws_lb_listener_rule" "services" {
  for_each = var.forwarding_rules

  listener_arn = aws_lb_listener.https.arn
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

# variables.tf

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

# outputs.tf

output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "The ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "target_group_arns" {
  description = "The ARNs of the target groups"
  value       = { for k, v in aws_lb_target_group.services : k => v.arn }
}