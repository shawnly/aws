variable "tag_key" {
  description = "The key of the tag used to filter the ACM certificate and EC2 instance"
  type        = string
  default     = "DomainEC2Map"
}

variable "tag_value" {
  description = "The value of the tag used to filter the ACM certificate and EC2 instance"
  type        = string
}
