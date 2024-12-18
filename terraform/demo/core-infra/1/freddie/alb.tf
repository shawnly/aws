resource "aws_lb" "private" {
  name               = "${var.project}-${var.environment}-${var.ec2_number}"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.https.id, aws_security_group.nessus.id]
  subnets           = var.private_subnets

  enable_deletion_protection = true

  idle_timeout = 4000

  tags = {
    Name        = "${var.project}-${var.environment}-alb-${var.event_id}"
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.private.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.default.arn
  }
}

resource "aws_lb_target_group" "default" {
  name     = "Default-tg-${var.project}-${var.event_id}"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    interval            = 6
    path                = "/"
    protocol            = "HTTP"
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}