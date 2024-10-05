variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "aws_profile" {
  description = "AWS CLI profile to use"
  type        = string
  default     = "default"
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, stage, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for the ALB and instances"
  type        = string
}

variable "listener_arn" {
  description = "The ARN of the ALB listener"
  type        = string
}

variable "forwarding_rules" {
  description = "List of forwarding rules configuration"
  type = list(object({
    name              = string
    forward_path      = string
    priority          = number
    port              = number
    health_check_path = string
    ec2_instance_id   = string
  }))
}
