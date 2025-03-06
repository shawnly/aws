#!/bin/bash

# Replace these variables with your actual values
ORG_NAME="your-organization-name"
GITHUB_TOKEN="your-github-personal-access-token"
HOOK_ID="webhook-id-from-list-response"

# Send a ping event to test the webhook
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/orgs/${ORG_NAME}/hooks/${HOOK_ID}/pings