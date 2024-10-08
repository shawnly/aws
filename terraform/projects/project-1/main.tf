# Provider definition (previously in provider.tf)
provider "aws" {
  profile = var.aws_profile
  region  = "us-east-1"  # Adjust as per your region
}

variable "aws_profile" {
  description = "The AWS CLI profile to use."
  type        = string
}

variable "domain_ec2_map" {
  description = "The combined domain, environment, and event ID."
  type        = string
}

variable "security_groups" {
  description = "List of security groups for the ALB."
  type        = list(string)
}


# Call to the internal-alb module (previously in main.tf)
module "internal_alb" {
  source          = "../../modules/internal-alb"
  aws_profile     = var.aws_profile
  domain_ec2_map  = var.domain_ec2_map
  security_groups = var.security_groups
}

# Output the ALB DNS name (previously in outputs.tf)
output "alb_dns_name" {
  description = "The DNS name of the internal ALB"
  value       = module.internal_alb.alb_dns_name
}

# Terraform version and provider version constraints (previously in version.tf)
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}
