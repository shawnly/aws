variable "aws_region" {
  description = "The AWS region to deploy resources"
  type        = string
}

variable "aws_profile" {
  description = "AWS CLI profile to use"
  type        = string
}

variable "project" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
}

variable "event_id" {
  description = "Event ID for tagging"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "private_subnets" {
  description = "List of private subnet IDs for resources"
  type        = list(string)
}

variable "private_subnet1" {
  description = "Single private subnet for specific EC2 placement"
  type        = string
}

variable "ec2_number" {
  description = "Identifier for EC2 instance"
  type        = string
}

variable "db_username" {
  description = "Username for the RDS database"
  type        = string
}

variable "db_password" {
  description = "Password for the RDS database"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class type"
  type        = string
  default     = "db.m5.large"
}

variable "db_storage_size" {
  description = "RDS storage size in GB"
  type        = number
  default     = 200
}
