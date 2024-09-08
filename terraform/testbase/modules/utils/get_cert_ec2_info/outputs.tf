output "cert_arn" {
  description = "The ARN of the ACM certificate"
  value       = data.aws_acm_certificate.selected_cert.arn
}

output "instance_id" {
  description = "The ID of the EC2 instance"
  value       = data.aws_instance.selected_instance.id
}

output "ip_address" {
  description = "The IP address of the EC2 instance"
  value       = data.aws_instance.selected_instance.public_ip
}
