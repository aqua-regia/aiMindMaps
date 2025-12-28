#!/bin/bash

# Run the web server version

# Check for virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Find Python command
PYTHON_CMD=""
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

# Run the web server
echo "Starting AI Mind Map Generator Web Server..."
PORT=${WEB_PORT:-8080}
echo "Open your browser to: http://localhost:$PORT"
echo "(Using port $PORT - set WEB_PORT env var to change)"
$PYTHON_CMD web_server.py

