# Provider configuration for AWS
provider "aws" {
  profile = var.aws_profile
}

# Fetch ACM certificate by tag
data "aws_acm_certificate" "selected_cert" {
  most_recent = true

  tags = {
    var.tag_key = var.tag_value
  }
}

# Fetch EC2 instance by tag
data "aws_instance" "selected_instance" {
  filter {
    name   = "tag:${var.tag_key}"
    values = [var.tag_value]
  }
}
