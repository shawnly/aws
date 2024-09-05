variable "region" {
  description = "The AWS region to use."
  type        = string
}

variable "aws_profile" {
  description = "The AWS CLI profile to use."
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC to fetch details for. If not provided, the default VPC will be used."
  type        = string
  default     = null
}
