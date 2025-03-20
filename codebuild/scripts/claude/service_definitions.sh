#!/bin/bash

# Define individual service lists
freddie_service_list=(
  "freddie-service1"
  "freddie-service2"
  "freddie-service3"
)

common_service_list=(
  "common-service1"
  "common-service2"
  "common-service3"
)

xtmclient_service_list=(
  "xtmclient-service1"
  "xtmclient-service2"
  "xtmclient-service3"
)

# Create parallel arrays for services and their origins
SERVICE_LIST=()
SERVICE_ORIGIN=()

# Add freddie services with origin information
for service in "${freddie_service_list[@]}"; do
  SERVICE_LIST+=("$service")
  SERVICE_ORIGIN+=("freddie_service_list")
done

# Add common services with origin information
for service in "${common_service_list[@]}"; do
  SERVICE_LIST+=("$service")
  SERVICE_ORIGIN+=("common_service_list")
done

# Add xtmclient services with origin information
for service in "${xtmclient_service_list[@]}"; do
  SERVICE_LIST+=("$service")
  SERVICE_ORIGIN+=("xtmclient_service_list")
done

# Export variables to make them available to other scripts
export SERVICE_LIST
export SERVICE_ORIGIN