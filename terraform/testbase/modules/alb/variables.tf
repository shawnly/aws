variable "project" {
  description = "The project name."
  type        = string
}

variable "environment" {
  description = "The environment (dev, prod, etc.)."
  type        = string
}

variable "web_security_group_id" {
  description = "Security group ID for the web tier."
  type        = string
}

variable "subnets" {
  description = "List of subnets where the ALB will be deployed."
  type        = list(string)
}

variable "vpc_id" {
  description = "The VPC ID where the ALB will be deployed."
  type        = string
}
