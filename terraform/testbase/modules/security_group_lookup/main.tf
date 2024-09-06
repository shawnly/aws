# Fetch security group by Name tag
data "aws_security_group" "https_sg" {
  filter {
    name   = "tag:Name"
    values = [var.security_group_tag_name]
  }

  # Optionally, you can pass a vpc_id if needed
  vpc_id = var.vpc_id
}