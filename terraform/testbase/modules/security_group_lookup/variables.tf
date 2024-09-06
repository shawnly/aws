variable "security_group_tag_name" {
  description = "The value of the Name tag for the security group"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID in which the security group resides (optional)"
  type        = string
  default     = null
}
