module "security_groups" {
  source      = "../../modules/security_groups"
  project     = var.project
  environment = var.environment
  event_id    = var.event_id
  vpc_id      = var.vpc_id
  vpccidr     = var.vpccidr
}
