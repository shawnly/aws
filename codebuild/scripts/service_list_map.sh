#!/bin/bash

# Declare associative array to map services to their respective lists
declare -A SERVICE_MAP

# Define individual service lists and populate SERVICE_MAP
freddie_service_list=("freddie_service1" "freddie_service2" "freddie_service3")
for service in "${freddie_service_list[@]}"; do
    SERVICE_MAP["$service"]="freddie_service_list"
done

common_service_list=("common_service1" "common_service2" "common_service3")
for service in "${common_service_list[@]}"; do
    SERVICE_MAP["$service"]="common_service_list"
done

xtmclient_service_list=("xtmclient_service1" "xtmclient_service2" "xtmclient_service3")
for service in "${xtmclient_service_list[@]}"; do
    SERVICE_MAP["$service"]="xtmclient_service_list"
done

# Merge all service lists into SERVICE_LIST
SERVICE_LIST=("${!SERVICE_MAP[@]}")
