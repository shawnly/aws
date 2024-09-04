resource "aws_security_group" "this" {
  name        = "${var.project}-${var.commit_id}"
  vpc_id      = var.vpc_id
  description = "Security group for ${var.project} project with commit ${var.commit_id}"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project}-${var.commit_id}"
    Project     = var.project
    CommitID    = var.commit_id
    Environment = var.environment
  }
}
