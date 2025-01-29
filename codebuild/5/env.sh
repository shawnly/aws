#!/bin/bash

# GitHub Enterprise Repository URL
export GITHUB_REPO_URL="https://github.enterprise.com/org/repo"

# VPC Configuration
export VPC_ID="vpc-xxxx"
export SUBNET_IDS="subnet-xxxx,subnet-yyyy"

# Optional: Other environment variables
export STACK_NAME="my-codebuild"
export GITHUB_TOKEN_PATH="/codebuild/github-enterprise-token"