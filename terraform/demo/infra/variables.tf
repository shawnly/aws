variable "region" {}
variable "project" {}
variable "environment" {}
variable "event_id" {}
variable "vpc_id" {}
variable "vpc_cidr" {}
variable "private_subnets" { type = list(string) }
variable "private_subnet" {}
variable "instance_type" {}
variable "ami_id" {}
variable "ec2_key_name" {}
variable "ecs_instance_profile" {}
variable "ec2_number" {}
