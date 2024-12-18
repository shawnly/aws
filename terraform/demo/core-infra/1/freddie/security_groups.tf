resource "aws_security_group" "nessus" {
  name_prefix = "${var.project}-${var.environment}-nessus-sg${var.event_id}"
  description = "Allow Nessus Scanner inbound traffic"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["128.102.4.216/32", "143.232.252.34/32", "128.102.195.216/32", "131.110.136.100/32"]
    description = "Nessus from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-nessus-sg-${var.event_id}"
  }
}