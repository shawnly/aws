service_lists.sh
#!/bin/bash

# Define service lists
freddie_service_list=(
  "freddie-service1"
  "freddie-service2"
  "freddie-service3"
)

common_service_list=(
  "common-service1"
  "common-service2"
  "common-service3" 
  "common-service4"
)

xtmclient_service_list=(
  "xtmclient-service1"
  "xtmclient-service2"
)

# Merge all service lists into one combined SERVICE_LIST
SERVICE_LIST=(
  "${freddie_service_list[@]}"
  "${common_service_list[@]}"
  "${xtmclient_service_list[@]}"
)