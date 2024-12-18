# modules/security_groups/variables.tf
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