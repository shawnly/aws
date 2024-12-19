# modules/ecs-service/main.tf
resource "aws_cloudwatch_log_group" "service" {
  name              = "${var.project}-${var.product}-${var.service_name}-service-LogGroup-${var.event_id}"
  retention_in_days = 1

  tags = {
    Environment = var.environment
    Project     = var.project
    Service     = var.service_name
  }
}

resource "aws_ecs_task_definition" "service" {
  family                   = "${var.project}-${var.product}-${var.service_name}-${var.event_id}"
  memory                   = var.container_memory
  requires_compatibilities = ["EC2"]
  network_mode            = "bridge"
  task_role_arn          = var.task_role_arn
  execution_role_arn     = var.execution_role_arn

  container_definitions = jsonencode([
    {
      name  = "${var.project}-${var.product}-${var.service_name}-service-${var.event_id}"
      image = var.service_image
      portMappings = [
        {
          containerPort = var.container_port
          hostPort     = var.host_port
          protocol     = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.service.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = var.service_name
        }
      }
      essential = true
      environment = [
        for k, v in local.environment_variables : {
          name  = k
          value = v
        }
      ]
      mountPoints = []
      volumesFrom = []
    }
  ])

  tags = {
    Environment = var.environment
    Project     = var.project
    Service     = var.service_name
  }
}

resource "aws_lb_target_group" "service" {
  name                          = "${var.project}-${var.service_name}-tg-${var.event_id}"
  port                          = var.host_port
  protocol                      = "HTTP"
  vpc_id                        = var.vpc_id
  deregistration_delay          = 5
  load_balancing_algorithm_type = "round_robin"

  health_check {
    enabled             = true
    healthy_threshold   = 3
    interval            = 30
    matcher             = "200"
    path                = var.health_check_path
    port                = var.host_port
    protocol            = "HTTP"
    timeout             = 6
    unhealthy_threshold = 10
  }

  tags = {
    Environment = var.environment
    Project     = var.project
    Service     = var.service_name
  }
}

resource "aws_lb_listener_rule" "service" {
  listener_arn = var.listener_arn
  priority     = var.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.service.arn
  }

  condition {
    path_pattern {
      values = [var.path_pattern]
    }
  }
}

resource "aws_ecs_service" "service" {
  name                               = "${var.project}-${var.product}-${var.service_name}-service-${var.event_id}"
  cluster                            = var.cluster_name
  task_definition                    = aws_ecs_task_definition.service.arn
  desired_count                      = var.desired_count
  health_check_grace_period_seconds  = 600
  launch_type                        = "EC2"

  load_balancer {
    target_group_arn = aws_lb_target_group.service.arn
    container_name   = "${var.project}-${var.product}-${var.service_name}-service-${var.event_id}"
    container_port   = var.container_port
  }

  deployment_configuration {
    maximum_percent         = 100
    minimum_healthy_percent = 0
  }

  tags = {
    Environment = var.environment
    Project     = var.project
    Service     = var.service_name
  }
}

# modules/ecs-service/variables.tf
variable "project" {
  description = "Name of project"
  type        = string
}

variable "product" {
  description = "Name of product"
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

variable "service_name" {
  description = "Service Name"
  type        = string
}

variable "cluster_name" {
  description = "Name of ECS Cluster"
  type        = string
}

variable "service_image" {
  description = "Name of docker Service Image"
  type        = string
}

variable "desired_count" {
  description = "The number of desired tasks"
  type        = number
  default     = 1
}

variable "container_memory" {
  description = "Container Memory"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8080
}

variable "host_port" {
  description = "Host port"
  type        = number
  default     = 0
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/actuator/health"
}

variable "path_pattern" {
  description = "Path pattern for routing"
  type        = string
}

variable "priority" {
  description = "Rule priority"
  type        = number
}

variable "spring_profiles" {
  description = "Spring profiles to activate"
  type        = string
  default     = ""
}

variable "client_id" {
  description = "Client ID"
  type        = string
}

variable "kafka_server" {
  description = "Kafka server address"
  type        = string
}

variable "database_name_prefix" {
  description = "Database name prefix"
  type        = string
}

variable "database_server" {
  description = "Database server address"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "dss_aud" {
  description = "DSS audience"
  type        = string
}

variable "dss_url" {
  description = "DSS URL"
  type        = string
}

variable "sdss_url" {
  description = "SDSS URL"
  type        = string
}

variable "token_manager_url" {
  description = "Token manager URL"
  type        = string
}

variable "fims_url" {
  description = "FIMS URL"
  type        = string
}

variable "interop_url" {
  description = "InterOp URL"
  type        = string
}

variable "bootstrap_servers" {
  description = "Bootstrap servers"
  type        = string
}

variable "schema_registry_url" {
  description = "Schema registry URL"
  type        = string
}

variable "schema_registry_auth_info" {
  description = "Schema registry auth info"
  type        = string
  sensitive   = true
}

variable "cc_user_password" {
  description = "CC user password"
  type        = string
  sensitive   = true
}

variable "cc_username" {
  description = "CC username"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the ECS Task Role"
  type        = string
}

variable "execution_role_arn" {
  description = "ARN of the ECS Task Execution Role"
  type        = string
}

variable "listener_arn" {
  description = "ARN of the ALB listener"
  type        = string
}

# modules/ecs-service/locals.tf
locals {
  environment_variables = {
    Environment                         = var.environment
    EventID                            = var.event_id
    SPRING_PROFILES_ACTIVE             = var.spring_profiles
    ClientID                           = var.client_id
    KafkaServer                        = var.kafka_server
    DatabaseNamePrefix                  = var.database_name_prefix
    DataBaseServer                     = var.database_server
    DBUserName                         = var.db_username
    DBPassword                         = var.db_password
    DSSAud                             = var.dss_aud
    DSSUrl                             = var.dss_url
    SDSSUrl                            = var.sdss_url
    TokenManagerUrl                    = var.token_manager_url
    FIMSUrl                            = var.fims_url
    InterOpUrl                         = var.interop_url
    BOOTSTRAP_SERVERS                  = var.bootstrap_servers
    SCHEMA_REGISTRY_URL                = var.schema_registry_url
    SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO = var.schema_registry_auth_info
    CC_USER_PASSWORD                   = var.cc_user_password
    CC_USER_NAME                       = var.cc_username
  }
}

# modules/ecs-service/data.tf
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# modules/ecs-service/outputs.tf
output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = aws_ecs_task_definition.service.arn
}

output "service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.service.name
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.service.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.service.name
}

# modules/ecs-service/versions.tf
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}