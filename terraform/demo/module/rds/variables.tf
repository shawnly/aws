variable "project" {
  description = "The name of the project"
}

variable "environment" {
  description = "The environment (e.g. dev, prod)"
}

variable "event_id" {
  description = "The event ID"
}

variable "vpc_id" {
  description = "The ID of the VPC"
}

variable "vpccidr" {
  description = "The CIDR block for the VPC"
}
