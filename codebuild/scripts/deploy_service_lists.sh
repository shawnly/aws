#!/bin/bash

# Source the primary script to import SERVICE_LIST and SERVICE_ORIGINS
source ./service_lists.sh

# Loop through each service in SERVICE_LIST
for i in "${!SERVICE_LIST[@]}"; do
    service="${SERVICE_LIST[$i]}"
    origin="${SERVICE_ORIGINS[$i]}"
    echo "Service '$service' belongs to '$origin'"
    # Add your deployment logic here
done
