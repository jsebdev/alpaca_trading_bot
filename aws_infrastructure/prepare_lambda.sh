#!/bin/bash

# Prepare bot code for Lambda deployment
# This script copies the trading bot code from the repository root to the Lambda package

set -e  # Exit on error

echo "Preparing bot code for Lambda deployment..."

# Clean previous build
if [ -d "lambda/bot_package" ]; then
    echo "Cleaning previous bot_package..."
    rm -rf lambda/bot_package
fi

# Create directory structure
echo "Creating bot_package directory..."
mkdir -p lambda/bot_package

# Copy bot code from repository root
echo "Copying bot modules..."
cp -r ../bots lambda/bot_package/
cp -r ../strategies lambda/bot_package/
cp -r ../utils lambda/bot_package/

# Verify the copy
echo ""
echo "Bot package structure:"
ls -la lambda/bot_package/

echo ""
echo "Bots directory:"
ls -la lambda/bot_package/bots/

echo ""
echo "Strategies directory:"
ls -la lambda/bot_package/strategies/

echo ""
echo "Utils directory:"
ls -la lambda/bot_package/utils/

# Count Python files
PYTHON_FILES=$(find lambda/bot_package -name "*.py" | wc -l)
echo ""
echo "Total Python files copied: $PYTHON_FILES"

echo ""
echo "Bot package prepared successfully!"
echo "Lambda deployment package structure:"
echo "lambda/"
echo "├── handler.py"
echo "└── bot_package/"
echo "    ├── bots/"
echo "    ├── strategies/"
echo "    └── utils/"
