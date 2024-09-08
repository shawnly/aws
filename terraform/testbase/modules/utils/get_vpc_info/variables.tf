variable "aws_profile" {
  description = "The AWS profile to use"
  type        = string
}

variable "aws_region" {
  description = "The AWS region to use"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "The ID of the VPC to retrieve information for"
  type        = string
}
