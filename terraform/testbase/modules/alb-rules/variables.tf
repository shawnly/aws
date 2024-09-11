variable "project" {
  description = "The project name"
  type        = string
}

variable "environment" {
  description = "The environment (dev, stage, prod)"
  type        = string
}

variable "listener_arn" {
  description = "The ARN of the ALB listener"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID where the target group is hosted"
  type        = string
}

variable "priority" {
  description = "The priority for the listener rule"
  type        = number
  default     = 100
}
