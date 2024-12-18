# variables.tf
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment for the project"
  type        = string
}

variable "event_id" {
  description = "Event ID for the project"
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
  description = "EC2 instance type"
  type        = string
  default     = "m5.large"
}

variable "ec2_key_name" {
  description = "EC2 Key Pair name"
  type        = string
  default     = "arc-af-etm-EAST"
}

variable "ecs_instance_profile" {
  description = "ECS Instance Profile"
  type        = string
  default     = "ARC-AF-ETM-SSM-EC2"
}

variable "domain_ec2_map" {
  description = "Domain EC2 Map"
  type        = string
}

variable "ec2_number" {
  description = "EC2 Number"
  type        = string
}