variable "name_prefix" {
  description = "Prefix for naming resources"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "allocated_storage" {
  description = "RDS storage in GB"
  type        = number
  default     = 100
}

variable "engine_version" {
  description = "RDS engine version"
  type        = string
  default     = "12.22"
}

variable "instance_type" {
  description = "RDS instance type"
  type        = string
  default     = "db.m5.xlarge"
}

variable "availability_zone" {
  description = "RDS availability zone"
  type        = string
}

variable "master_username" {
  description = "RDS master username"
  type        = string
  default     = "postgres"
}

variable "db_subnet_group_name" {
  description = "RDS DB subnet group name"
  type        = string
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
}
