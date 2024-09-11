provider "aws" {
  region = "us-west-2"  # Change to your region
}

resource "aws_lb_target_group" "ec2_tg" {
  name        = "${var.project}-${var.environment}-tg"
  port        = 23701                             # Overwrite traffic port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id                        # VPC ID passed in as a parameter
  target_type = "ip"

  health_check {
    path                = "/xxx/actuator/info"    # Health check path
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group_attachment" "tg_attachment" {
  target_group_arn = aws_lb_target_group.ec2_tg.arn
  target_id        = "131.129.18.167"             # EC2 instance IP address
  port             = 23701                        # Forward traffic to this port
}

resource "aws_lb_listener_rule" "forward_rule" {
  listener_arn = var.listener_arn                 # Passed listener ARN
  priority     = var.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ec2_tg.arn
  }

  condition {
    path_pattern {
      values = ["/xxx/actuator/info"]
    }
  }
}
