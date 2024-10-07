variable "DomainEC2Map" {
  description = "Map for domain, environment, and EC2 identifier"
  type        = string
}

variable "forwarding_rules" {
  description = "List of forwarding rules with paths, ports, and health checks"
  type = list(object({
    name              = string
    forward_path      = string
    priority          = number
    port              = number
    health_check_path = string
    response_code     = string
  }))
}

variable "vpc_id" {
  description = "VPC ID for the target group"
  type        = string
}
