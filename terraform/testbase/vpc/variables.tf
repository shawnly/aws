variable "aws_profile" {
  description = "The AWS CLI profile to use"
  type        = string
}

variable "aws_region" {
  description = "The AWS region to operate in"
  type        = string
  default     = "us-west-2"
}

variable "vpc_name" {
  description = "The name of the VPC to look up"
  type        = string
}
