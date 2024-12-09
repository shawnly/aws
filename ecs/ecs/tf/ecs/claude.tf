# Project Structure:
# 
# terraform-ecs-deployment/
# ├── main.tf
# ├── variables.tf
# ├── outputs.tf
# ├── versions.tf
# └── modules/
#     └── ecs_cluster/
#         ├── main.tf
#         ├── variables.tf
#         └── outputs.tf

# Root Directory: main.tf
provider "aws" {
  region = var.region
}

module "ecs_cluster" {
  source = "./modules/ecs_cluster"

  # Common Variables
  environment_name = var.environment_name
  vpc_id           = var.vpc_id
  subnet_ids       = var.subnet_ids

  # EC2 Instance Configuration
  instance_type    = var.instance_type
  key_pair_name    = var.key_pair_name

  # Microservice Configuration
  microservice_docker_image = var.microservice_docker_image
}

# Root Directory: variables.tf
variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-west-2"
}

variable "environment_name" {
  description = "Name of the environment"
  type        = string
  default     = "ecs-deployment"
}

variable "vpc_id" {
  description = "VPC ID for deployment"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_pair_name" {
  description = "EC2 Key Pair Name"
  type        = string
}

variable "microservice_docker_image" {
  description = "Docker image for microservice"
  type        = string
}

# Root Directory: outputs.tf
output "ecs_cluster_name" {
  description = "Name of the ECS Cluster"
  value       = module.ecs_cluster.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS Cluster"
  value       = module.ecs_cluster.cluster_arn
}

# Root Directory: versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Module Directory: modules/ecs_cluster/main.tf
resource "aws_security_group" "ecs_cluster" {
  name        = "${var.environment_name}-ecs-sg"
  description = "Security group for ECS cluster instances"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "ecs_instance_role" {
  name = "${var.environment_name}-ecs-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_instance_role_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
  role       = aws_iam_role.ecs_instance_role.name
}

resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "${var.environment_name}-ecs-instance-profile"
  role = aws_iam_role.ecs_instance_role.name
}

resource "aws_launch_template" "ecs_launch_template" {
  name = "${var.environment_name}-ecs-launch-template"

  iam_instance_profile {
    name = aws_iam_instance_profile.ecs_instance_profile.name
  }

  image_id      = "ami-0c55b159cbfafe1f0"  # Amazon ECS-Optimized AMI
  instance_type = var.instance_type
  key_name      = var.key_pair_name

  vpc_security_group_ids = [aws_security_group.ecs_cluster.id]

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    cluster_name = aws_ecs_cluster.main.name
  }))
}

resource "aws_autoscaling_group" "ecs_asg" {
  desired_capacity    = 1
  max_size            = 3
  min_size            = 1
  vpc_zone_identifier = var.subnet_ids

  launch_template {
    id      = aws_launch_template.ecs_launch_template.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.environment_name}-ecs-instance"
    propagate_at_launch = true
  }
}

resource "aws_ecs_cluster" "main" {
  name = "${var.environment_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_capacity_provider" "main" {
  name = "${var.environment_name}-capacity-provider"

  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.ecs_asg.arn
    managed_scaling {
      maximum_scaling_step_size = 1000
      minimum_scaling_step_size = 1
      status                    = "ENABLED"
      target_capacity           = 100
    }
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = [aws_ecs_capacity_provider.main.name]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = aws_ecs_capacity_provider.main.name
  }
}

resource "aws_ecs_task_definition" "microservice" {
  family                   = "${var.environment_name}-microservice"
  network_mode             = "bridge"
  requires_compatibilities = ["EC2"]

  container_definitions = jsonencode([{
    name  = "microservice"
    image = var.microservice_docker_image
    portMappings = [{
      containerPort = 80
      hostPort      = 80
    }]
    memoryReservation = 256
  }])
}

resource "aws_ecs_service" "microservice" {
  name            = "${var.environment_name}-microservice-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.microservice.arn
  desired_count   = 1
  launch_type     = "EC2"
}

# Module Directory: modules/ecs_cluster/variables.tf
variable "environment_name" {
  description = "Name of the environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for deployment"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_pair_name" {
  description = "EC2 Key Pair Name"
  type        = string
}

variable "microservice_docker_image" {
  description = "Docker image for microservice"
  type        = string
}

# Module Directory: modules/ecs_cluster/outputs.tf
output "cluster_name" {
  description = "Name of the ECS Cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS Cluster"
  value       = aws_ecs_cluster.main.arn
}

# Module Directory: modules/ecs_cluster/templates/user_data.sh
#!/bin/bash
echo ECS_CLUSTER=${cluster_name} >> /etc/ecs/ecs.config
yum update -y
yum install -y awslogs
systemctl start awslogsd
systemctl enable awslogsd.service