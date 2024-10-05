resource "aws_lb_listener_rule" "microservice_forwarding_rule" {
  count        = length(var.forwarding_rules)
  listener_arn = var.listener_arn

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.microservice_target_group[count.index].arn
  }

  condition {
    path_pattern {
      values = [var.forwarding_rules[count.index].forward_path]
    }
  }

  priority = var.forwarding_rules[count.index].priority
}

resource "aws_lb_target_group" "microservice_target_group" {
  count       = length(var.forwarding_rules)
  name = lower(replace("${var.project}-${var.environment}-${var.forwarding_rules[count.index].name}", "_", "-"))
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
  }
}

resource "aws_lb_target_group_attachment" "ec2_attachment" {
  count = length(var.forwarding_rules)

  target_group_arn = aws_lb_target_group.microservice_target_group[count.index].arn
  target_id        = var.forwarding_rules[count.index].ec2_instance_id
  port             = var.forwarding_rules[count.index].port
}
