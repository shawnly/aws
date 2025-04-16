#!/bin/bash

# Source the primary script to import SERVICE_LIST
source ./service_list.sh

# Loop through each service in SERVICE_LIST
for service in "${SERVICE_LIST[@]}"; do
    echo "Processing $service"
    # Add your processing logic here
done
