# main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = [var.vpc_name]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }

  tags = {
    Tier = "Private"
  }
}

data "aws_instances" "selected" {
  filter {
    name   = "tag:DomainEC2Map"
    values = [var.DomainEC2Map]
  }
}

data "aws_acm_certificate" "selected" {
  domain   = var.domain_name
  statuses = ["ISSUED"]
  most_recent = true
}

module "alb" {
  source = "./modules/alb"

  DomainEC2Map      = var.DomainEC2Map
  event_id          = var.event_id
  security_group_ids = var.security_group_ids
  forwarding_rules  = var.forwarding_rules
  vpc_id            = data.aws_vpc.selected.id
  subnet_ids        = data.aws_subnets.private.ids
  create_alb        = var.create_alb
  certificate_arn   = data.aws_acm_certificate.selected.arn
  instance_ids      = data.aws_instances.selected.ids
}

# variables.tf

variable "aws_profile" {
  description = "AWS profile to use for authentication"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "vpc_name" {
  description = "Name tag of the VPC to use"
  type        = string
}

variable "DomainEC2Map" {
  description = "Combined string of domain-environment-ec2"
  type        = string
}

variable "event_id" {
  description = "Event ID for the ALB"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs for the ALB"
  type        = list(string)
}

variable "forwarding_rules" {
  description = "Map of forwarding rules for services"
  type = map(object({
    path          = string
    priority      = number
    target_port   = number
    health_path   = string
    response_code = string
  }))
}

variable "create_alb" {
  description = "Whether to create a new ALB or use an existing one"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for the SSL certificate"
  type        = string
}

# outputs.tf

output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = module.alb.alb_dns_name
}

output "alb_arn" {
  description = "The ARN of the load balancer"
  value       = module.alb.alb_arn
}

output "target_group_arns" {
  description = "The ARNs of the target groups"
  value       = module.alb.target_group_arns
}

output "listener_arn" {
  description = "The ARN of the HTTPS listener"
  value       = module.alb.listener_arn
}