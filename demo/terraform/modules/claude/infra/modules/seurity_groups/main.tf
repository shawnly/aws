resource "aws_security_group" "nessus" {
  name        = "${var.project}-${var.environment}-nessus-sg${var.event_id}"
  description = "Allow Nessus Scanner inbound traffic"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [
      "128.102.4.216/32", 
      "143.232.252.34/32", 
      "128.102.195.216/32", 
      "131.110.136.100/32"
    ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-nessus-sg-${var.event_id}"
  }
}

resource "aws_security_group" "https" {
  name        = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  description = "HTTPS access from internal"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [
      "156.68.0.0/16",
      "143.232.0.0/16",
      "129.168.0.0/16",
      "128.102.0.0/16",
      var.vpc_cidr,
      "128.102.147.81/32"
    ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  }
}

resource "aws_security_group" "ssh" {
  name        = "${var.project}-${var.environment}-ssh-nessus-sg${var.event_id}"
  description = "SSH access from internal IP"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [
      "156.68.0.0/16",
      "143.232.0.0/16",
      "128.102.149.49/32",
      "128.102.147.81/32",
      var.vpc_cidr
    ]
  }

  # Nessus related ingress rules
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [
      "128.102.4.216/32", 
      "143.232.252.34/32", 
      "128.102.195.216/32", 
      "131.110.136.100/32"
    ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-ssh-sg${var.event_id}"
  }
}

resource "aws_security_group" "freddie" {
  name        = "${var.project}-${var.environment}-freddie-sg-${var.event_id}"
  description = "Security Group from ALB to NPSU"
  vpc_id      = var.vpc_id

  # Multiple port ingress rules
  dynamic "ingress" {
    for_each = {
      "op-api" = 10203
      "ph-utm" = 10220
      "as-utm" = 8091
      "inter-op-api-utm" = 10206
      "token-manager" = 10200
      "cm" = 10204
      "ddp" = 8090
      "constrains-interface-1" = 9131
      "constrains-interface-2" = 9132
    }
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = [var.vpc_cidr]
      description = ingress.key
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-freddie-sg-${var.event_id}"
  }
}

# Additional security groups would follow a similar pattern