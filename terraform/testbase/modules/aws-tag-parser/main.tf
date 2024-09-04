locals {
  # Split the tag_value by hyphen
  parts = split("-", var.tag_value)
  
  # Assign the parts to variables
  project = local.parts[0]
  env     = local.parts[1]
  number  = local.parts[2]
}