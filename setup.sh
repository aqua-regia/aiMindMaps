#!/bin/bash

# AI Mind Map Generator - Setup Script
# This script automates the installation process

set -e  # Exit on error

echo "=========================================="
echo "AI Mind Map Generator - Setup"
echo "=========================================="
echo ""

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    if ! command -v "$python_cmd" &> /dev/null; then
        return 1
    fi
    
    local version_output=$($python_cmd --version 2>&1)
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    local version=$(echo $version_output | awk '{print $2}')
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    
    if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
        return 0
    fi
    
    return 1
}

# Check Python version
echo "Checking Python version..."
PYTHON_CMD=""

# Try different Python commands in order of preference
for cmd in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
    if check_python_version "$cmd"; then
        PYTHON_CMD="$cmd"
        python_version=$($cmd --version 2>&1 | awk '{print $2}')
        echo "Found Python $python_version using '$cmd'"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "❌ ERROR: Python 3.8 or higher is required but not found."
    echo ""
    echo "Checking for Python in common locations..."
    
    # Check for pyenv
    if command -v pyenv &> /dev/null; then
        echo "  Found pyenv. Available Python versions:"
        pyenv versions --bare 2>/dev/null | grep -E "^3\.[89]|^3\.1[0-2]" | head -5 | while read version; do
            echo "    - python$version"
        done
        echo ""
        echo "  To use a specific pyenv version:"
        echo "    pyenv local 3.9  # or 3.10, 3.11, etc."
        echo "    ./setup.sh"
    fi
    
    # Check for Homebrew Python on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ -d "/opt/homebrew/bin" ] || [ -d "/usr/local/bin" ]; then
            echo "  Checking Homebrew installations..."
            for brew_dir in /opt/homebrew/bin /usr/local/bin; do
                if [ -d "$brew_dir" ]; then
                    for brew_python in "$brew_dir"/python3.*; do
                        if [ -f "$brew_python" ] && check_python_version "$brew_python"; then
                            echo "    Found: $brew_python"
                        fi
                    done
                fi
            done
        fi
    fi
    
    echo ""
    echo "Please install Python 3.8 or higher:"
    echo "  • macOS: brew install python@3.9 (or python@3.10, python@3.11)"
    echo "  • Ubuntu/Debian: sudo apt-get install python3.9"
    echo "  • Using pyenv: pyenv install 3.9 && pyenv local 3.9"
    echo "  • Or download from: https://www.python.org/downloads/"
    echo ""
    echo "If you have Python 3.8+ installed but it's not in PATH, you can:"
    echo "  1. Specify the Python command: PYTHON_CMD=python3.9 ./setup.sh"
    echo "  2. Or create an alias: alias python3=python3.9"
    echo ""
    exit 1
fi

# Allow override via environment variable
if [ -n "$PYTHON_CMD_OVERRIDE" ]; then
    if check_python_version "$PYTHON_CMD_OVERRIDE" > /dev/null 2>&1; then
        PYTHON_CMD="$PYTHON_CMD_OVERRIDE"
        python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
        echo "Using specified Python: $python_version"
    else
        echo "⚠️  WARNING: Specified Python ($PYTHON_CMD_OVERRIDE) doesn't meet requirements"
        echo "   Falling back to: $PYTHON_CMD"
    fi
fi

echo "✓ Python version is compatible"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Create output directory
echo "Creating output directory..."
mkdir -p output
echo "✓ Output directory created"
echo ""

# Check for .env file
echo "Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ Created .env file from template"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env and add your DEEPSEEK_API_KEY"
        echo "   You can get your API key from: https://platform.deepseek.com/"
    else
        echo "⚠️  WARNING: .env.example not found. Please create .env manually"
    fi
else
    echo "✓ .env file already exists"
fi
echo ""

# Check if API key is set
if [ -f ".env" ]; then
    if grep -q "DEEPSEEK_API_KEY=your_deepseek_api_key_here" .env || ! grep -q "DEEPSEEK_API_KEY=" .env; then
        echo "⚠️  WARNING: DEEPSEEK_API_KEY not configured in .env"
        echo "   Please edit .env and add your API key before running the application"
    else
        echo "✓ DEEPSEEK_API_KEY found in .env"
    fi
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If not done already, edit .env and add your DEEPSEEK_API_KEY"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the application: $PYTHON_CMD main.py"
echo ""
echo "To activate the virtual environment in the future:"
echo "  source venv/bin/activate"
echo ""
echo "Note: Using Python $python_version ($PYTHON_CMD)"
echo ""

