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
Continuing `rds.tf`:
```hcl
resource "aws_db_instance" "postgresql" {
  identifier           = "${var.project}-${var.environment}-${var.event_id}"
  engine               = "postgres"
  engine_version       = "12.22"
  instance_class      = var.db_instance_class
  allocated_storage   = var.db_storage_size
  storage_type        = "gp2"
  
  username            = var.rds_username
  password            = var.rds_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  publicly_accessible    = false
  multi_az              = false
  deletion_protection   = true
  backup_retention_period = 7
  
  tags = {
    Name        = "${var.project}-PostgreSQL"
    Project     = var.project
    Environment = var.environment
  }
}
```

7. `outputs.tf` - Output Definitions:
```hcl
output "nessus_security_group_id" {
  description = "NESSUS Security Group ID"
  value       = aws_security_group.nessus.id
}

output "https_security_group_id" {
  description = "HTTPS Security Group ID"
  value       = aws_security_group.https.id
}

output "ssh_security_group_id" {
  description = "SSH Security Group ID"
  value       = aws_security_group.ssh.id
}

output "freddie_security_group_id" {
  description = "Freddie Security Group ID"
  value       = aws_security_group.freddie.id
}

output "rds_security_group_id" {
  description = "RDS Security Group ID"
  value       = aws_security_group.rds.id
}

output "fims_dss_security_group_id" {
  description = "FIMS DSS Security Group ID"
  value       = aws_security_group.fims_dss.id
}

output "xtm_client_security_group_id" {
  description = "XTM Client Security Group ID"
  value       = aws_security_group.xtm_client.id
}

output "whitelist_security_group_id" {
  description = "WhiteList Security Group ID"
  value       = aws_security_group.whitelist.id
}

output "private_load_balancer_arn" {
  description = "The ARN of the private load balancer"
  value       = aws_lb.private.arn
}

output "private_load_balancer_dns" {
  description = "The DNS name of the private load balancer"
  value       = aws_lb.private.dns_name
}

output "http_listener_arn" {
  description = "The ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}

output "db_endpoint" {
  description = "The connection endpoint for the database"
  value       = aws_db_instance.postgresql.endpoint
}

output "db_port" {
  description = "The port on which the database accepts connections"
  value       = aws_db_instance.postgresql.port
}
```

8. `terraform.tfvars.example` - Example Variables File:
```hcl
project        = "myproject"
environment    = "dev"
event_id       = "001"
vpc_id         = "vpc-xxxxx"
vpc_cidr       = "10.0.0.0/16"
private_subnets = ["subnet-xxxxx", "subnet-yyyyy"]
private_subnet_1 = "subnet-xxxxx"
region         = "us-east-1"
domain_ec2_map = "map1"

# RDS Configuration
db_instance_class = "db.m5.xlarge"
db_storage_size   = 200
rds_username      = "postgres"
rds_password      = "your-secure-password"
```

9. Deployment Instructions:

Create a new file called `README.md`:
```markdown
# Infrastructure Terraform Module

This Terraform module deploys a complete infrastructure stack including:
- Security Groups
- Application Load Balancer
- ECS Cluster with EC2 instance
- RDS PostgreSQL database

## Prerequisites

1. Terraform v1.0.0 or newer
2. AWS CLI configured with appropriate credentials
3. VPC and subnets already created
4. Appropriate IAM permissions

## Deployment Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a `terraform.tfvars` file:
```bash
cp terraform.tfvars.example terraform.tfvars
```

3. Edit `terraform.tfvars` with your specific values:
- Update VPC and subnet IDs
- Set appropriate project and environment names
- Configure RDS settings
- Set appropriate CIDR ranges

4. Initialize Terraform:
```bash
terraform init
```

5. Review the deployment plan:
```bash
terraform plan
```

6. Apply the configuration:
```bash
terraform apply
```

7. Confirm the changes by typing `yes` when prompted

## Post-Deployment

1. Store the outputs securely, especially database endpoints and security group IDs
2. Verify all security groups are correctly configured
3. Test the load balancer health check endpoint
4. Verify ECS cluster is running properly
5. Test database connectivity

## Destruction (if needed)

Note: The RDS instance has deletion protection enabled. To delete:

1. First modify the RDS instance to disable deletion protection:
```bash
aws rds modify-db-instance --db-instance-identifier <instance-id> --no-deletion-protection
```

2. Then run:
```bash
terraform destroy
```

## Common Issues and Troubleshooting

1. VPC Dependency Issues:
   - Ensure all subnet IDs are correct
   - Verify VPC CIDR ranges

2. Security Group Issues:
   - Check if all required ports are open
   - Verify CIDR ranges are correct

3. RDS Issues:
   - Verify subnet group configuration
   - Check security group rules

4. Load Balancer Issues:
   - Verify subnet configurations
   - Check security group attachments

## Maintenance

1. Regular Updates:
   - Keep Terraform version updated
   - Regularly update provider versions
   - Review and update AMI IDs

2. Monitoring:
   - Set up CloudWatch alarms for RDS metrics
   - Monitor ECS cluster metrics
   - Check ALB access logs
```

This completes the conversion of the CloudFormation template to Terraform. The module is organized into logical files for better maintenance and readability. The README provides comprehensive deployment instructions and troubleshooting guidance.

To use this module:
1. Follow the deployment instructions in the README
2. Ensure all variables are properly set in terraform.tfvars
3. Use the outputs to integrate with other parts of your infrastructure
4. Monitor the deployed resources using AWS Console or CloudWatch

Would you like me to explain any specific part in more detail?