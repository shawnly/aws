# Output the DNS name of the ALB
output "alb_dns_name" {
  description = "The DNS name of the internal ALB"
  value       = aws_lb.internal_alb.dns_name
}
