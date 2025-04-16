#!/bin/bash

# Source the primary script to import SERVICE_LIST and SERVICE_MAP
source ./service_list_map.sh

# Loop through each service in SERVICE_LIST
for service in "${SERVICE_LIST[@]}"; do
    service_list="${SERVICE_MAP[$service]}"
    echo "Service '$service' belongs to '$service_list'"
    # Add your deployment logic here
done
