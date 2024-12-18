```
infrastructure-module/
│
├── README.md                  # Module documentation and deployment instructions
│
├── versions.tf                # Terraform and provider versions
├── variables.tf              # Input variable declarations
├── outputs.tf                # Output declarations
│
├── security_groups.tf        # All security group resources
├── load_balancer.tf          # ALB and related resources
├── ecs.tf                    # ECS cluster and EC2 instance
├── rds.tf                    # RDS PostgreSQL instance and subnet group
│
├── terraform.tfvars.example  # Example variable definitions
│
├── .gitignore               # Git ignore file
│
└── examples/                 # Example implementations
    └── complete/            # Complete example
        ├── main.tf          # Main configuration
        ├── variables.tf     # Example-specific variables
        ├── outputs.tf       # Example-specific outputs
        └── README.md        # Example-specific documentation
```

Additional files that should be included in `.gitignore`:
```gitignore
# .gitignore content
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!terraform.tfvars.example
.terraform.lock.hcl
*.backup
*.log
```

Each file serves a specific purpose:

1. Root Directory Files:
   - `versions.tf`: Provider configurations and version constraints
   - `variables.tf`: All input variable declarations
   - `outputs.tf`: All output value declarations
   - `terraform.tfvars.example`: Example variable values

2. Resource Files:
   - `security_groups.tf`: All security group definitions
   - `load_balancer.tf`: ALB and related resources
   - `ecs.tf`: ECS cluster and EC2 configurations
   - `rds.tf`: RDS PostgreSQL configurations

3. Documentation:
   - `README.md`: Main module documentation
   - `examples/complete/README.md`: Example-specific documentation

4. Example Implementation:
   - The `examples/complete` directory shows how to use the module in a real-world scenario

Best practices for this structure:
1. Keep resource types grouped in their own files
2. Maintain clear separation between variable declarations and their values
3. Include comprehensive documentation
4. Provide working examples
5. Use consistent file naming
6. Keep sensitive information out of version control

Would you like me to provide the content for any of these additional files, such as the example implementation or .gitignore?