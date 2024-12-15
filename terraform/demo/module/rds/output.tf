output "nessus_sg_id" {
  value = aws_security_group.nessus_sg.id
}

output "https_sg_id" {
  value = aws_security_group.https_sg.id
}

output "ssh_sg_id" {
  value = aws_security_group.ssh_sg.id
}

output "freddie_sg_id" {
  value = aws_security_group.freddie_sg.id
}

output "rds_sg_id" {
  value = aws_security_group.rds_sg.id
}

output "fims_dss_sg_id" {
  value = aws_security_group.fims_dss_sg.id
}

output "xtm_client_sg_id" {
  value = aws_security_group.xtm_client_sg.id
}

output "white_list_sg_id" {
  value = aws_security_group.white_list_sg.id
}
