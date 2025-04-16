#!/bin/bash

# Define individual service lists
freddie_service_list=("freddie_service1" "freddie_service2" "freddie_service3")
common_service_list=("common_service1" "common_service2" "common_service3")
xtmclient_service_list=("xtmclient_service1" "xtmclient_service2" "xtmclient_service3")

# Initialize SERVICE_LIST and SERVICE_ORIGINS
SERVICE_LIST=()
SERVICE_ORIGINS=()

# Populate SERVICE_LIST and SERVICE_ORIGINS
for service in "${freddie_service_list[@]}"; do
    SERVICE_LIST+=("$service")
    SERVICE_ORIGINS+=("freddie_service_list")
done

for service in "${common_service_list[@]}"; do
    SERVICE_LIST+=("$service")
    SERVICE_ORIGINS+=("common_service_list")
done

for service in "${xtmclient_service_list[@]}"; do
    SERVICE_LIST+=("$service")
    SERVICE_ORIGINS+=("xtmclient_service_list")
done
