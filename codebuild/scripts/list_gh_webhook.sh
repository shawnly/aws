#!/bin/bash

# Replace these variables with your actual values
ORG_NAME="your-organization-name"
GITHUB_TOKEN="your-github-personal-access-token"

# List all existing webhooks
curl -X GET \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/orgs/${ORG_NAME}/hooks