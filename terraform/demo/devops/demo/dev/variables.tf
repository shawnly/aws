variable "project" {
  description = "The name of the project (e.g., example-project)"
  type        = string
}

variable "environment" {
  description = "The environment name (e.g., dev, prod)"
  type        = string
}

variable "event_id" {
  description = "Unique identifier for the event"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "vpccidr" {
  description = "The CIDR block for the VPC"
  type        = string
}
