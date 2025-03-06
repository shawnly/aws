#!/bin/bash

# Replace these variables with your actual values
ORG_NAME="your-organization-name"
GITHUB_TOKEN="your-github-personal-access-token"
WEBHOOK_URL="your-aws-codebuild-webhook-payload-url"
WEBHOOK_SECRET="your-aws-codebuild-webhook-secret"

# Create the webhook using GitHub API
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/orgs/${ORG_NAME}/hooks \
  -d '{
    "name": "web",
    "active": true,
    "events": [
      "push",
      "pull_request"
    ],
    "config": {
      "url": "'"${WEBHOOK_URL}"'",
      "content_type": "json",
      "secret": "'"${WEBHOOK_SECRET}"'",
      "insecure_ssl": "0"
    }
  }'