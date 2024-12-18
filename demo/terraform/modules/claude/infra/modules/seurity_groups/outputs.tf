# modules/security_groups/outputs.tf
output "nessus_sg_id" {
  description = "ID of the Nessus Security Group"
  value       = aws_security_group.nessus.id
}

output "https_sg_id" {
  description = "ID of the HTTPS Security Group"
  value       = aws_security_group.https.id
}

output "ssh_sg_id" {
  description = "ID of the SSH Security Group"
  value       = aws_security_group.ssh.id
}

output "freddie_sg_id" {
  description = "ID of the Freddie Security Group"
  value       = aws_security_group.freddie.id
}