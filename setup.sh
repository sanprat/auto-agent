#!/bin/bash
# setup.sh - Initializer script for Personal AI OS (aios)

set -e

echo "=== Initializing Personal AI OS (aios) environment ==="

# 1. Create subfolders
mkdir -p configs database memory telegram orchestrator planner workers verifier scheduler logs skills experiments

# 2. Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 could not be found. Please install Python 3.9+."
    exit 1
fi

# 3. Setup virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
else
    echo "Virtual environment 'venv' already exists."
fi

# 4. Activate venv & install base packages
source venv/bin/activate
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Playwright setup if required
# To avoid force-slowing the build, we let the user install it as an optional layer
echo "To install Playwright browser worker dependencies (optional), run:"
echo "  pip install playwright && playwright install"

echo ""
echo "=== Environment Setup Completed! ==="
echo "To start the OS:"
echo "  1. Update configs/config.yaml with your credentials."
echo "  2. Activate virtual environment: source venv/bin/activate"
echo "  3. Run the OS: python main.py"
echo "====================================="
