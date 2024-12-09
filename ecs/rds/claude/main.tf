# environments/dev/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "rds" {
  source = "../../modules/rds"

  project_name     = var.project_name
  environment      = "dev"
  vpc_id           = var.vpc_id
  subnet_ids       = var.subnet_ids
  instance_type    = var.instance_type
  storage_size     = var.storage_size
  engine_version   = var.engine_version

  tags = {
    Project     = var.project_name
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}