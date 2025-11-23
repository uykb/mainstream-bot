#!/bin/bash

# Replace the following placeholders with your actual credentials
export BINANCE_API_KEY="your_binance_api_key"
export BINANCE_API_SECRET="your_binance_api_secret"
export LARK_WEBHOOK_URL="your_lark_webhook_url"
export GEMINI_API_KEY="your_gemini_api_key"

# Run the Docker container with the environment variables
docker run -d \
  -e BINANCE_API_KEY=$BINANCE_API_KEY \
  -e BINANCE_API_SECRET=$BINANCE_API_SECRET \
  -e LARK_WEBHOOK_URL=$LARK_WEBHOOK_URL \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  your_image_name:latest
