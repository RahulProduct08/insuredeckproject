#!/bin/bash

# Temple Quest - Installation Helper for Mac/Linux
# This script installs all dependencies

echo ""
echo "============================================================"
echo ""
echo "  🏛️  TEMPLE QUEST - Installation Helper 🏛️"
echo ""
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo ""
    echo "Please install Python from: https://www.python.org/downloads/"
    echo "Or use your package manager:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo ""
    exit 1
fi

echo "✅ Python found!"
echo ""
python3 --version
echo ""

# Install requirements
echo "Installing dependencies..."
echo ""
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install dependencies!"
    echo ""
    exit 1
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "============================================================"
echo ""
echo "🎮 CHOOSE YOUR VERSION:"
echo ""
echo "1. Web Version (Browser)"
echo "   Command: python3 mario_india_web.py"
echo "   Then open: http://localhost:5000"
echo ""
echo "2. Desktop Version"
echo "   Command: python3 mario_india_game_enhanced.py"
echo ""
echo "============================================================"
echo ""
