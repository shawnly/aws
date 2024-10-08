# Input variables for the ALB
variable "aws_profile" {
  type        = string
  description = "AWS profile to use for finding vpc_id and subnets."
}

variable "domain_ec2_map" {
  type        = string
  description = "Combined parameter in the format project-environment-event_id."
}

variable "security_groups" {
  type        = list(string)
  description = "List of security groups for the ALB."
}
