provider "aws" {
  region = var.region
}

### SECURITY GROUPS ###
resource "aws_security_group" "nessus" {
  name        = "${var.project}-${var.environment}-nessus-sg-${var.event_id}"
  description = "Allow Nessus Scanner inbound traffic"
  vpc_id      = var.vpc_id

  ingress = [
    { description = "Nessus Scanner 1", from_port = 0, to_port = 65535, protocol = "tcp", cidr_blocks = ["128.102.4.216/32"] },
    { description = "Nessus Scanner 2", from_port = 0, to_port = 65535, protocol = "tcp", cidr_blocks = ["143.232.252.34/32"] },
    { description = "Nessus Scanner 3", from_port = 0, to_port = 65535, protocol = "tcp", cidr_blocks = ["128.102.195.216/32"] },
    { description = "Nessus Scanner 4", from_port = 0, to_port = 65535, protocol = "tcp", cidr_blocks = ["131.110.136.100/32"] },
  ]

  egress = [{ from_port = 0, to_port = 0, protocol = "-1", cidr_blocks = ["0.0.0.0/0"] }]

  tags = {
    Name = "${var.project}-${var.environment}-nessus-sg-${var.event_id}"
  }
}

resource "aws_security_group" "https" {
  name        = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  description = "HTTPS access security group"
  vpc_id      = var.vpc_id

  ingress = [
    { description = "HTTPS VPN", from_port = 443, to_port = 443, protocol = "tcp", cidr_blocks = ["156.68.0.0/16"] },
    { description = "HTTPS LAN", from_port = 443, to_port = 443, protocol = "tcp", cidr_blocks = [var.vpc_cidr] },
  ]

  egress = [{ from_port = 0, to_port = 0, protocol = "-1", cidr_blocks = ["0.0.0.0/0"] }]

  tags = {
    Name = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  }
}

### ALB ###
resource "aws_lb" "private_lb" {
  name               = "${var.project}-${var.environment}-${var.ec2_number}"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.https.id, aws_security_group.nessus.id]
  subnets            = var.private_subnets

  tags = {
    Name = "${var.project}-${var.environment}-${var.ec2_number}"
  }
}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.private_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type   = "text/plain"
      message_body   = "${var.project}-${var.environment}-ALB is healthy"
      status_code    = "200"
    }
  }
}

### ECS CLUSTER ###
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "${var.project}-${var.environment}-ecs-${var.event_id}"
}

resource "aws_instance" "ecs_instance" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.private_subnet
  key_name               = var.ec2_key_name
  iam_instance_profile   = var.ecs_instance_profile
  associate_public_ip_address = false

  tags = {
    Name = "${var.project}-${var.environment}-${var.event_id}"
  }

  user_data = <<EOF
#!/bin/bash
echo ECS_CLUSTER=${var.project}-${var.environment}-ecs-${var.event_id} >> /etc/ecs/ecs.config
EOF
}
