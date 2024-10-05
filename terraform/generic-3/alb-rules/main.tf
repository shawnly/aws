# Parse DomainEC2Map into domain, environment, and ec2
locals {
  domain      = split("-", var.DomainEC2Map)[0]
  environment = split("-", var.DomainEC2Map)[1]
  ec2         = split("-", var.DomainEC2Map)[2]
}

# Use the parsed domain and environment to find the EC2 instance by tag
data "aws_instance" "selected_ec2" {
  filter {
    name   = "tag:DomainEC2Map"
    values = [var.DomainEC2Map]
  }

  count = 1
}

# Reference the selected EC2 instance ID
resource "aws_lb_target_group" "microservice_target_group" {
  count = length(var.forwarding_rules)

  name = lower(replace("${local.domain}-${local.environment}-${var.forwarding_rules[count.index].name}", "_", "-"))

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

  target {
    id = data.aws_instance.selected_ec2[0].id
    port = var.forwarding_rules[count.index].port
  }
}
