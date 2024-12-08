provider "aws" {
  region = "us-east-1" # Update as needed
}

module "rds" {
  source                 = "./modules/rds"
  name_prefix            = "my-project"
  vpc_id                 = "vpc-0example" # Update to your VPC ID
  allocated_storage      = 100
  engine_version         = "12.22"
  instance_type          = "db.m5.xlarge"
  availability_zone      = "us-east-1a"
  db_subnet_group_name   = "my-db-subnet-group" # Update to your DB Subnet Group name
  master_username        = "postgres"
  tags = {
    Environment = "Production"
    Project     = "MyProject"
  }
}
