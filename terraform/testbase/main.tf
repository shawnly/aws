provider "aws" {
  region = "us-east-1"
}

# Call the security group lookup module to get the security group ID by tag
module "get_https_security_group" {
  source = "./modules/security_group_lookup"

  security_group_tag_name = "nussus_https"
  vpc_id                  = "your-vpc-id"  # Optional if you have multiple VPCs
}

# Output for debugging
output "https_security_group_id" {
  value = module.get_https_security_group.security_group_id
}
