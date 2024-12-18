resource "aws_ecs_cluster" "main" {
  name = "${var.project}-${var.environment}-ecs-${var.event_id}"
}

resource "aws_instance" "ecs" {
  instance_type = var.instance_type
  ami           = "ami-075e0bc7e13861a3f"  # This should be parameterized or data-sourced
  key_name      = var.key_name

  iam_instance_profile = var.ecs_instance_profile

  network_interface {
    network_interface_id = aws_network_interface.ecs.id
    device_index        = 0
  }

  user_data = base64encode(<<-EOF
              #!/bin/bash
              rm -f /etc/ecs/ecs.config
              echo ECS_CLUSTER=${var.project}-${var.environment}-ecs-${var.event_id} >> /etc/ecs/ecs.config
              EOF
  )

  tags = {
    Name          = "${var.project}-${var.environment}-${var.event_id}"
    DomainEC2Map  = var.domain_ec2_map
  }
}

resource "aws_network_interface" "ecs" {
  subnet_id       = var.private_subnet_1
  security_groups = [aws_security_group.freddie.id]
}