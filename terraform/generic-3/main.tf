module "alb_forwarding_rules" {
  source = "./alb-rules"

  aws_region      = var.aws_region
  aws_profile     = var.aws_profile
  project         = var.project
  environment     = var.environment
  vpc_id          = var.vpc_id
  listener_arn    = var.listener_arn
  forwarding_rules = var.forwarding_rules
}
