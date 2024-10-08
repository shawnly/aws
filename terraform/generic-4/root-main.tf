module "internal_alb" {
  source          = "./modules/internal-alb" # Update the path to the module
  aws_profile     = "your_aws_profile"
  domain_ec2_map  = "project-environment-01"
  security_groups = ["sg-0123456789abcdef0"] # Replace with your actual security group IDs
}
