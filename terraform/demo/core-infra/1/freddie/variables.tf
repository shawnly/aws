variable "project" {
  description = "Name of project"
  type        = string
}

variable "environment" {
  description = "Environment for this project"
  type        = string
}

variable "domain_ec2_map" {
  description = "Environment for this project"
  type        = string
}

variable "ec2_number" {
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
  description = "VPC CIDR"
  type        = string
}

variable "private_subnets" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "private_subnet_1" {
  description = "Primary private subnet ID"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "m5.large"
}

variable "key_name" {
  description = "Name of EC2 key pair"
  type        = string
  default     = "arc-af-etm-EAST"
}

variable "ecs_instance_profile" {
  description = "Name of Instance profile"
  type        = string
  default     = "ARC-AF-ETM-SSM-EC2"
}

variable "db_instance_class" {
  description = "Database instance type"
  type        = string
  default     = "db.m5.xlarge"
}

variable "db_storage_size" {
  description = "Storage size in GB"
  type        = number
  default     = 200
}

variable "rds_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "rds_username" {
  description = "RDS master username"
  type        = string
  default     = "postgres"
}