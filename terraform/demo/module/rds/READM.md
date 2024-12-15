dev/main.tf

module "security_groups" {
  source      = "../../modules/security_groups"
  project     = var.project
  environment = var.environment
  event_id    = var.event_id
  vpc_id      = var.vpc_id
  vpc_cidr    = var.vpc_cidr
}

dev/terraform.tfvars
project     = "example-project"
environment = "dev"
event_id    = "01"
vpc_id      = "vpc-123456"
vpc_cidr    = "10.0.0.0/16"
