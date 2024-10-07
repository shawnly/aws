# Parse DomainEC2Map into domain, environment, and ec2
locals {
  domain      = split("-", var.DomainEC2Map)[0]
  environment = split("-", var.DomainEC2Map)[1]
  ec2         = split("-", var.DomainEC2Map)[2]
}

# Find the ALB with the tag DomainEC2Map
data "aws_lb" "alb" {
  filter {
    name   = "tag:DomainEC2Map"
    values = [var.DomainEC2Map]
  }

  count = 1
}

# Find the ACM certificate with the tag DomainEC2Map
data "aws_acm_certificate" "cert" {
  filter {
    name   = "tag:DomainEC2Map"
    values = [var.DomainEC2Map]
  }

  most_recent = true
}

# Find existing HTTP listener if available
data "aws_lb_listener" "http_listener" {
  load_balancer_arn = data.aws_lb.alb[0].arn
  port              = 80
  protocol          = "HTTP"
}

# Create HTTPS listener if it does not already exist
resource "aws_lb_listener" "https_listener" {
  count = length(data.aws_lb_listener.http_listener) == 0 ? 1 : 0

  load_balancer_arn = data.aws_lb.alb[0].arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = data.aws_acm_certificate.cert.arn
}

# Define target group for each forwarding rule
resource "aws_lb_target_group" "microservice_target_group" {
  count = length(var.forwarding_rules)

  name = lower(replace("${local.domain}-${local.environment}-${var.forwarding_rules[count.index].name}-tg", "_", "-"))

  port        = var.forwarding_rules[count.index].port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    path                = var.forwarding_rules[count.index].health_check_path
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
    matcher             = var.forwarding_rules[count.index].response_code
  }
}

# Attach the EC2 instance to the corresponding target group
resource "aws_lb_target_group_attachment" "tg_attachment" {
  count = length(var.forwarding_rules)

  target_group_arn = aws_lb_target_group.microservice_target_group[count.index].arn
  target_id        = data.aws_instance.selected_ec2[0].id
  port             = var.forwarding_rules[count.index].port
}

# Add forwarding rules to HTTP listener if exists
resource "aws_lb_listener_rule" "http_forwarding_rule" {
  count = length(data.aws_lb_listener.http_listener) > 0 ? length(var.forwarding_rules) : 0

  listener_arn = data.aws_lb_listener.http_listener[0].arn
  priority     = var.forwarding_rules[count.index].priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.microservice_target_group[count.index].arn
  }

  condition {
    path_pattern {
      values = [var.forwarding_rules[count.index].forward_path]
    }
  }
}

# Add forwarding rules to HTTPS listener if created
resource "aws_lb_listener_rule" "https_forwarding_rule" {
  count = length(aws_lb_listener.https_listener) > 0 ? length(var.forwarding_rules) : 0

  listener_arn = aws_lb_listener.https_listener[0].arn
  priority     = var.forwarding_rules[count.index].priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.microservice_target_group[count.index].arn
  }

  condition {
    path_pattern {
      values = [var.forwarding_rules[count.index].forward_path]
    }
  }
}
