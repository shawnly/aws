resource "aws_security_group" "nessus_sg" {
  name_prefix = "${var.project}-${var.environment}-nessus-sg-${var.event_id}"
  description = "Allow Nessus Scanner inbound traffic"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [
      "128.102.4.216/32", "143.232.252.34/32", "128.102.195.216/32", "131.110.136.100/32"
    ]
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

resource "aws_security_group" "https_sg" {
  name_prefix = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  description = "https access from internal"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [
      "156.68.0.0/16", "143.232.0.0/16", "129.168.0.0/16", "128.102.0.0/16", "!Ref VPCCIDR", "128.102.147.81/32"
    ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-https-sg-${var.event_id}"
  }
}

resource "aws_security_group" "ssh_sg" {
  name_prefix = "${var.project}-${var.environment}-ssh-sg-${var.event_id}"
  description = "ssh access from internal IP"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [
      "156.68.0.0/16", "143.232.0.0/16", "128.102.149.49/32", "128.102.147.81/32", "!Ref VPCCIDR",
      "128.102.4.216/32", "143.232.252.34/32", "128.102.195.216/32", "131.110.136.100/32"
    ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-ssh-sg-${var.event_id}"
  }
}

resource "aws_security_group" "freddie_sg" {
  name_prefix = "${var.project}-${var.environment}-freddie-sg-${var.event_id}"
  description = "Security Group from ALB to NPSU"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 10203
    to_port     = 10203
    protocol    = "tcp"
    cidr_blocks = ["!Ref VPCCIDR"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-freddie-sg-${var.event_id}"
  }
}

resource "aws_security_group" "rds_sg" {
  name_prefix = "${var.project}-${var.environment}-rds-sg-${var.event_id}"
  description = "Security group from EC2 to RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["!Ref VPCCIDR"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-rds-sg-${var.event_id}"
  }
}

resource "aws_security_group" "fims_dss_sg" {
  name_prefix = "${var.project}-${var.environment}-fims-dss-sg-${var.event_id}"
  description = "Security group from ALB to FIMS and DSS"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8082
    to_port     = 8082
    protocol    = "tcp"
    cidr_blocks = ["!Ref VPCCIDR"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-fims-dss-sg-${var.event_id}"
  }
}

resource "aws_security_group" "xtm_client_sg" {
  name_prefix = "${var.project}-${var.environment}-xtmclient-sg-${var.event_id}"
  description = "alb target group access xtmclient"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["!Ref VPCCIDR"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-xtmclient-sg-${var.event_id}"
  }
}

resource "aws_security_group" "white_list_sg" {
  name_prefix = "${var.project}-${var.environment}-white-list-sg-${var.event_id}"
  description = "https access from pattern IPs"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-${var.environment}-white-list-sg-${var.event_id}"
  }
}
