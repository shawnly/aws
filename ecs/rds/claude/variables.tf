# environments/dev/variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "myproject"
}

variable "vpc_id" {
  description = "VPC ID for deployment"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for RDS"
  type        = list(string)
}

variable "instance_type" {
  description = "RDS instance type"
  type        = string
  default     = "db.m5.xlarge"
}

variable "storage_size" {
  description = "Storage size in GB"
  type        = number
  default     = 200
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "12.22-R1"
}