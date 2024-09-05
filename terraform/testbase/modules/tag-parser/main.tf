data "aws_vpc" "selected" {
  count = var.vpc_id != null ? 1 : 0
  id    = var.vpc_id
}

data "aws_vpcs" "all" {
  count = var.vpc_id == null ? 1 : 0
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected[0].id]
  }
  depends_on = [data.aws_vpc.selected]
}
