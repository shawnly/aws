# Parsing the DomainEC2Map and creating the ALB with listener and rules
locals {
  domain      = split("-", var.domain_ec2_map)[0]
  environment = split("-", var.domain_ec2_map)[1]
  event_id    = split("-", var.domain_ec2_map)[2]
}

resource "aws_lb" "internal_alb" {
  name               = "${local.domain}-${local.environment}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = var.security_groups
  subnets            = data.aws_subnets.selected.ids
}

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
