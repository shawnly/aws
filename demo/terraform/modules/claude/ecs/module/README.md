├── modules/
│   ├── infrastructure/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── ecs-service/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── data.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars


cd environments/dev
terraform init
terraform plan -target=module.infrastructure
terraform apply -target=module.infrastructure

then
terraform plan
terraform apply
