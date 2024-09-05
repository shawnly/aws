# Create the Application Load Balancer
resource "aws_lb" "this" {
  name               = "${var.project}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.web_security_group_id]
  subnets            = var.subnets
  enable_deletion_protection = false

  tags = {
    Name        = "${var.project}-${var.environment}-alb"
    Project     = var.project
    Environment = var.environment
  }
}

# Create a target group for the ALB (forwards to the backend)
resource "aws_lb_target_group" "this" {
  name     = "${var.project}-${var.environment}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.project}-${var.environment}-tg"
    Project     = var.project
    Environment = var.environment
  }
}

# Create a target group for fixed response (default action)
resource "aws_lb_target_group" "fixed_response" {
  name     = "${var.project}-${var.environment}-fixed-response-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 2
  }
}

# Create a listener for the ALB on port 80 (forward to the target group)
resource "aws_lb_listener" "this" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# Add a listener rule for a fixed response (for invalid URLs)
resource "aws_lb_listener_rule" "fixed_response_rule" {
  listener_arn = aws_lb_listener.this.arn
  priority     = 100  # Lower number = higher priority

  action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "You got the wrong URL"
      status_code  = "404"
    }
  }

  condition {
    host_header {
      values = ["*"]
    }
  }
}
