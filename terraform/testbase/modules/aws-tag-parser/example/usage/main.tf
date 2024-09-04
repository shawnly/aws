module "tags_parser" {
  source = "../../"

  tag_value = "xsv-dev-01"
}

output "project" {
  value = module.tags_parser.project
}

output "env" {
  value = module.tags_parser.env
}

output "number" {
  value = module.tags_parser.number
}