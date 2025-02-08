import os
import yaml
import re
from collections import OrderedDict

def process_yaml_files(directory):
    # Dictionary to store all configurations
    all_configs = OrderedDict()
    
    # Get all yaml files and sort them
    yaml_files = [f for f in os.listdir(directory) if f.endswith(('.yml', '.yaml'))]
    yaml_files.sort()  # Sort files alphabetically
    
    # Pattern to match the file naming convention
    pattern = r'application-datasource-([^-]+)-([^-]+)-([^.]+)\.ya?ml'
    
    # Process each yaml file in sorted order
    for filename in yaml_files:
        match = re.match(pattern, filename)
        if match:
            product, environment, project = match.groups()
            print(f"Processing file: {filename}")  # Added for visibility
            
            # Read and parse the YAML file
            with open(os.path.join(directory, filename), 'r') as file:
                config = yaml.safe_load(file)
            
            # Extract database information
            if 'spring' in config and 'datasource' in config['spring']:
                datasource = config['spring']['datasource']
                key = (product, project, environment)
                all_configs[key] = {
                    'host_port': datasource.get('host-port', ''),
                    'username': datasource.get('username', ''),
                    'password': datasource.get('password', '')
                }
    
    return all_configs

def generate_shell_script(configs):
    script = """#!/bin/bash

if [ $# -ne 3 ]; then
    echo "Usage: $0 <product> <project> <environment>"
    exit 1
fi

product=$1
project=$2
environment=$3

"""
    
    # Add case statement for product-project-environment combinations
    script += "case \"${product}-${project}-${environment}\" in\n"
    
    # Process configurations in sorted order
    for (product, project, environment), config in configs.items():
        case_key = f"{product}-{project}-{environment}"
        script += f"    \"{case_key}\")\n"
        script += f"        export DB_HOST_PORT={config['host_port']}\n"
        script += f"        export DB_USERNAME={config['username']}\n"
        script += f"        export DB_PASSWORD={config['password']}\n"
        # Add echo statements to show the variables
        script += "        echo \"\\$DB_HOST_PORT=$DB_HOST_PORT\"\n"
        script += "        echo \"\\$DB_USERNAME=$DB_USERNAME\"\n"
        script += "        echo \"\\$DB_PASSWORD=$DB_PASSWORD\"\n"
        script += "        ;;\n"
    
    script += """    *)
        echo "No configuration found for ${product}-${project}-${environment}"
        exit 1
        ;;
esac
"""
    
    return script

def main():
    # Get the current directory
    current_dir = os.getcwd()
    
    # Process YAML files
    configs = process_yaml_files(current_dir)
    
    # Generate shell script
    shell_script = generate_shell_script(configs)
    
    # Write the shell script to file
    with open('get-db-info.sh', 'w') as file:
        file.write(shell_script)
    
    # Make the script executable
    os.chmod('get-db-info.sh', 0o755)
    
    print("Successfully generated get-db-info.sh")

if __name__ == "__main__":
    main()