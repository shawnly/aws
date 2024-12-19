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
