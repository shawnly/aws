#!/bin/bash

# Function to get CloudFormation stack by tag
get_stack_by_tag() {
    local TAG_KEY=$1
    local TAG_VALUE=$2
    
    # Return the stack name that matches the tag
    aws cloudformation describe-stacks \
      --query "Stacks[?Tags[?Key=='$TAG_KEY' && Value=='$TAG_VALUE']].StackName" \
      --output text
}

# caller script

#!/bin/bash

# Source the file with the function
source ./get_stack_by_tag.sh

# Use the function
TAG_KEY="Environment"
TAG_VALUE="Production"
STACK_NAME=$(get_stack_by_tag "$TAG_KEY" "$TAG_VALUE")

echo "Stack name: $STACK_NAME"

# Continue with your script using $STACK_NAME

#inline script call

#!/bin/bash

# Set your tag key and value
TAG_KEY="Environment"
TAG_VALUE="Production"

# Get the stack name directly
STACK_NAME=$(aws cloudformation describe-stacks \
  --query "Stacks[?Tags[?Key=='$TAG_KEY' && Value=='$TAG_VALUE']].StackName" \
  --output text)

echo "Stack name: $STACK_NAME"

# Continue with your script using $STACK_NAME