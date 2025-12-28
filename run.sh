#!/bin/bash

# Simple script to run the AI Mind Map Generator

# Check for virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Find Python command
PYTHON_CMD=""

# Check for pyenv first
if command -v pyenv &> /dev/null; then
    # Try to use pyenv's Python
    for version in 3.12 3.11 3.10 3.9 3.8; do
        if pyenv which python$version &> /dev/null; then
            PYTHON_CMD=$(pyenv which python$version)
            version_output=$($PYTHON_CMD --version 2>&1)
            echo "Using Python $version_output (via pyenv)"
            break
        fi
    done
fi

# If pyenv didn't work, try system Python
if [ -z "$PYTHON_CMD" ]; then
    for cmd in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
        if command -v "$cmd" &> /dev/null; then
            version=$($cmd --version 2>&1 | awk '{print $2}')
            major=$(echo $version | cut -d. -f1)
            minor=$(echo $version | cut -d. -f2)
            if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
                PYTHON_CMD="$cmd"
                echo "Using Python $version"
                break
            fi
        fi
    done
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.8+ not found"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please edit .env and add your DEEPSEEK_API_KEY"
    fi
fi

# Run the application
echo "Starting AI Mind Map Generator..."
$PYTHON_CMD main.py

