#!/bin/bash

# Set your GitHub email
GITHUB_EMAIL="your_email@example.com"

# Generate SSH key
echo "Generating SSH key..."
ssh-keygen -t ed25519 -C "$GITHUB_EMAIL" -f ~/.ssh/id_ed25519 -N ""

# Start the ssh-agent
echo "Starting ssh-agent..."
eval "$(ssh-agent -s)"

# Add SSH key to the agent
ssh-add ~/.ssh/id_ed25519

# Display public key and instructions
echo ""
echo "✅ Public key generated. Add this key to GitHub:"
echo "-----------------------------------------------"
cat ~/.ssh/id_ed25519.pub
echo "-----------------------------------------------"
echo ""
echo "👉 Go to https://github.com/settings/keys to paste this key."
echo ""

# Test the connection
echo "Testing connection to GitHub..."
ssh -T git@github.com
