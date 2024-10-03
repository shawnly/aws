# main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Provider configuration
provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region
}

# Data source to get the VPC ID
data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["${var.vpc_name}"]
  }
}

# Data source to get the private subnets
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }

  tags = {
    Tier = "Private"
  }
}

# ALB module
module "alb" {
  source = "./modules/alb"  # Adjust this path to where you store the ALB module

  DomainEC2Map      = var.DomainEC2Map
  event_id          = var.event_id
  security_group_ids = var.security_group_ids
  forwarding_rules  = var.forwarding_rules

  # Pass the looked-up VPC ID and subnet IDs to the module
  vpc_id     = data.aws_vpc.selected.id
  subnet_ids = data.aws_subnets.private.ids
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

# outputs.tf

output "vpc_id" {
  description = "The ID of the VPC used"
  value       = data.aws_vpc.selected.id
}

output "subnet_ids" {
  description = "The IDs of the subnets used"
  value       = data.aws_subnets.private.ids
}

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