project     = "myproject"
environment = "dev"
vpc_id      = "vpc-12345678"
listener_arn = "arn:aws:elasticloadbalancing:region:account-id:listener/app/my-alb/50dc6c495c0c9188/9f9b5f2d5b5b5b55"

forwarding_rules = [
  {
    name              = "service_a"
    forward_path      = "/service-a/*"
    priority          = 300
    port              = 9090
    health_check_path = "/service-a/health"
    ec2_instance_id   = "i-1234567890abcdef0"
  },
  {
    name              = "service_b"
    forward_path      = "/service-b/*"
    priority          = 20301
    port              = 9091
    health_check_path = "/service-b/health"
    ec2_instance_id   = "i-0abcdef1234567890"
  }
]
