variable "vpc_id" {
  description = "The VPC ID where the security group will be created."
  type        = string
}

variable "vpc_cidr" {
  description = "The CIDR range of the VPC."
  type        = string
}

variable "project" {
  description = "The project name."
  type        = string
}

variable "commit_id" {
  description = "The commit ID for the project deployment."
  type        = string
}

variable "environment" {
  description = "The environment for the deployment (dev, prod, etc.)."
  type        = string
}
