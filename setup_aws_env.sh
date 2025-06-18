#!/bin/bash

# Set up environment variables for AWS deployment
echo "Setting up environment variables for AWS deployment..."

# You can either set these directly or read from .env file
if [ -f .env ]; then
    echo "Loading from .env file..."
    # Use source to properly handle quoted values with spaces
    set -a  # automatically export all variables
    source .env
    set +a  # turn off automatic export
else
    echo "Please enter your email configuration:"
    read -p "Sender Email (Gmail): " SENDER_EMAIL
    read -s -p "App Password: " APP_PASSWORD
    echo
    read -p "Recipient Email: " RECIPIENT_EMAIL
    
    export SENDER_EMAIL
    export APP_PASSWORD
    export RECIPIENT_EMAIL
fi

echo "Environment variables set:"
echo "SENDER_EMAIL: $SENDER_EMAIL"
echo "RECIPIENT_EMAIL: $RECIPIENT_EMAIL"
echo "APP_PASSWORD: [hidden]"

echo "✅ Environment variables ready for deployment!" 