variable "aws_profile" {
  type        = string
  description = "AWS profile to use"
}

variable "tag_name" {
  type        = string
  default     = "DomainEC2Map"
}

variable "tag_value" {
  type        = string
  default     = "xsv-dev-01"
}