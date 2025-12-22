#!/bin/bash

# Build Lambda Layer for Alpaca trading bot dependencies
# This script uses Docker to build dependencies compatible with AWS Lambda (Amazon Linux 2)

set -e  # Exit on error

echo "Building Lambda Layer for trading bot dependencies..."

# Create layer directory structure
echo "Creating layer directory structure..."
mkdir -p layers/python/lib/python3.12/site-packages

# Build dependencies using Lambda Python 3.12 Docker image
# This ensures binary compatibility with AWS Lambda runtime
echo "Installing dependencies using Docker..."
docker run --rm \
  -v "$(pwd)/layers:/layers" \
  -w /layers \
  public.ecr.aws/lambda/python:3.12 \
  pip install \
    alpaca-py==0.43.2 \
    python-dotenv==1.1.0 \
    pandas==2.3.3 \
    numpy==2.3.5 \
    sseclient-py==1.8.0 \
    websockets==15.0.1 \
    -t /layers/python/lib/python3.12/site-packages \
    --no-cache-dir

echo "Lambda layer built successfully!"
echo "Layer contents:"
ls -lh layers/python/lib/python3.12/site-packages/ | head -n 20

# Calculate layer size
LAYER_SIZE=$(du -sh layers | cut -f1)
echo "Total layer size: $LAYER_SIZE"

echo ""
echo "Note: If Docker is not available, you can use pip with --platform flag:"
echo "  pip install [packages] --platform manylinux2014_x86_64 --only-binary=:all: -t layers/python/lib/python3.12/site-packages"
