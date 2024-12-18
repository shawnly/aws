I'll create the following files:

1. `versions.tf` - Terraform and provider configurations
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.region  # You'll need to define this in variables.tf
}
```

2. `variables.tf` - Input variables
```hcl
variable "project" {
  description = "Name of project"
  type        = string
}

variable "environment" {
  description = "Environment for this project"
  type        = string
}

variable "event_id" {
  description = "Event ID for this project"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "private_subnets" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "private_subnet_1" {
  description = "First private subnet ID"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type for ECS"
  type        = string
  default     = "m5.large"
}

variable "ec2_key_name" {
  description = "EC2 Key Pair name for SSH access"
  type        = string
  default     = "arc-af-etm-EAST"
}

variable "ecs_instance_profile" {
  description = "IAM Instance Profile for ECS"
  type        = string
  default     = "ARC-AF-ETM-SSM-EC2"
}

variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.m5.xlarge"
  validation {
    condition     = contains(["db.m5.xlarge", "db.m6.xlarge"], var.db_instance_class)
    error_message = "Invalid DB instance class."
  }
}

variable "db_storage_size" {
  description = "Storage size in GB for RDS"
  type        = number
  default     = 200
  validation {
    condition     = contains([200, 400], var.db_storage_size)
    error_message = "Invalid DB storage size."
  }
}

variable "rds_username" {
  description = "RDS Master Username"
  type        = string
  default     = "postgres"
}

variable "rds_password" {
  description = "RDS Master Password"
  type        = string
  sensitive   = true
}

variable "domain_ec2_map" {
  description = "Domain EC2 Mapping"
  type        = string
}

variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}
```

3. `security_groups.tf` - Security Group Definitions
```hcl
# Nessus Security Group
resource "aws_security_group" "nessus" {
  name        = "${var.project}-${var.environment}-nessus-sg${var.event_id}"
  description = "Allow Nessus Scanner inbound traffic"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = ["128.102.4.216/32", "143.232.252.34/32", "128.102.195.216/32", "131.110.136.100/32"]
    content {
      from_port   = 0
      to_port     = 65535
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
      description = "Nessus from VPC"
    }
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

# HTTPS Security Group
resource "aws_security_group" "https" {
  name        = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  description = "HTTPS access from internal"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = [
      "156.68.0.0/16", 
      "143.232.0.0/16", 
      "129.168.0.0/16", 
      "128.102.0.0/16", 
      var.vpc_cidr,
      "128.102.147.81/32"
    ]
    content {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
      description = "HTTPS from various networks"
    }
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

# SSH Security Group
resource "aws_security_group" "ssh" {
  name        = "${var.project}-${var.environment}-ssh-nessus-sg${var.event_id}"
  description = "SSH access from internal IP"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = [
      "156.68.0.0/16", 
      "143.232.0.0/16", 
      "128.102.149.49/32", 
      "128.102.147.81/32", 
      var.vpc_cidr,
      "128.102.4.216/32",
      "143.232.252.34/32",
      "128.102.195.216/32",
      "131.110.136.100/32"
    ]
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [ingress.value]
      description = "SSH from various networks"
    }
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

# Freddie Security Group
resource "aws_security_group" "freddie" {
  name        = "${var.project}-${var.environment}-freddie-sg-${var.event_id}"
  description = "Security Group for Freddie services"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = {
      "op-api"              = 10203
      "ph-utm"              = 10220
      "as-utm"              = 8091
      "inter-op-api-utm"    = 10206
      "token-manager"       = 10200
      "cm"                  = 10204
      "ddp"                 = 8090
      "constrains-interface1" = 9131
      "constrains-interface2" = 9132
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

# RDS Security Group
resource "aws_security_group" "rds" {
  name        = "${var.project}-${var.environment}-rds-sg${var.event_id}"
  description = "Security Group from EC2 to RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "PostgreSQL access from VPC"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "SSH access from VPC"
  }

  tags = {
    Name = "${var.project}-${var.environment}-rds-sg${var.event_id}"
  }
}

# Additional Security Groups (FIMS, DSS, XTM Client, WhiteList)
resource "aws_security_group" "fims_dss" {
  name        = "${var.project}-${var.environment}-fims-dss-sg-${var.event_id}"
  description = "Security Group for FIMS and DSS"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = {
      "dss"     = 8082
      "fims"    = 23701
      "oauth2"  = 23700
    }
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = [var.vpc_cidr]
      description = ingress.key
    }
  }

  tags = {
    Name = "${var.project}-${var.environment}-fims-dss-sg-${var.event_id}"
  }
}

resource "aws_security_group" "xtm_client" {
  name        = "${var.project}-${var.environment}-xtmclient-sg-${var.event_id}"
  description = "Security Group for XTM Client"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = {
      "postgres"     = 5432
      "xtmclient"    = 4200
      "batch-server" = 8031
      "socket-io"    = 8033
      "oauth2"       = 23700
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
    Name = "${var.project}-${var.environment}-xtmclient-sg-${var.event_id}"
  }
}

resource "aws_security_group" "whitelist" {
  name        = "${var.project}-${var.environment}-white-list-sg-${var.event_id}"
  description = "WhiteList Security Group"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project}-${var.environment}-white-list-sg-${var.event_id}"
  }
}
```

4. `load_balancer.tf` - Load Balancer Configuration
```hcl
resource "aws_lb" "private" {
  name               = "${var.project}-${var.environment}-${var.domain_ec2_map}"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.https.id, aws_security_group.nessus.id]
  subnets            = var.private_subnets

  enable_deletion_protection = true

  idle_timeout = 4000

  # Additional load balancer attributes
  enable_http2 = true

  tags = {
    Name = "${var.project}-${var.environment}-alb"
  }
}

resource "aws_lb_target_group" "default" {
  name     = "Default-tg-${var.project}-${var.event_id}"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 6
    matcher             = "200"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.private.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.default.arn
  }
}

resource "aws_lb_listener_rule" "health" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "${var.project}-${var.environment}-alb-${var.event_id} http is health"
      status_code  = "200"
    }
  }

  condition {
    path_pattern {
      values = ["/alb-health"]
    }
  }
}
```

5. `ecs.tf` - ECS and EC2 Configuration
```hcl
resource "aws_ecs_cluster" "main" {
  name = "${var.project}-${var.environment}-ecs-${var.event_id}"
}

resource "aws_instance" "ecs" {
  ami           = "ami-075e0bc7e13861a3f"  # Hardcoded AMI, replace with your appropriate AMI
  instance_type = var.instance_type
  key_name      = var.ec2_key_name

  iam_instance_profile = var.ecs_instance_profile

  subnet_id  = var.private_subnet_1
  vpc_security_group_ids = [aws_security_group.freddie.id]

  user_data = base64encode(<<-EOF
    #!/bin/bash
    rm -f /etc/ecs/ecs.config
    echo ECS_CLUSTER=${aws_ecs_cluster.main.name} >> /etc/ecs/ecs.config
    EOF
  )

  tags = {
    Name           = "${var.project}-${var.environment}-${var.event_id}"
    DomainEC2Map   = var.domain_ec2_map
  }
}
```

6. `rds.tf` - RDS PostgreSQL Configuration
```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnets

  tags = {
    Name = "${var.project}-${var.environment}-db-subnet-group"
  }
}

resource "aws_db_instance" "postgresql" {
  identifier           = "${var.project}-${var.environment}-${var.event_id}"
  engine               = "postgres"
  engine_version       = "12.22"
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_storage