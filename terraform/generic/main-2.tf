# modules/alb/main.tf

# ... (keep the existing terraform and locals blocks)

# Remove the data blocks for VPC and subnets, as we'll now receive these as variables

resource "aws_lb" "main" {
  name               = "${local.domain}-${local.environment}-${var.event_id}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids  # Use the passed subnet IDs

  tags = {
    Name        = "${local.domain}-${local.environment}-${var.event_id}-alb"
    Environment = local.environment
    Project     = local.domain
  }
}

# ... (keep the existing aws_lb_listener block)

resource "aws_lb_target_group" "services" {
  for_each = var.forwarding_rules

  name     = "${local.domain}-${local.environment}-${each.key}"
  port     = each.value.target_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id  # Use the passed VPC ID

  health_check {
    path                = each.value.health_path
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = each.value.response_code
  }
}

# ... (keep the existing aws_lb_target_group_attachment and aws_lb_listener_rule blocks)

# modules/alb/variables.tf

# ... (keep the existing variables)

variable "vpc_id" {
  description = "The ID of the VPC to use"
  type        = string
}

variable "subnet_ids" {
  description = "The IDs of the subnets to use"
  type        = list(string)
}

# modules/alb/outputs.tf
# ... (keep the existing outputs)