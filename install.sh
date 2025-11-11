#!/bin/bash
# Quick Installation Script for Linux/macOS
echo "Installing Vosk-based Interpreter Helper..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from your package manager or python.org"
    exit 1
fi

echo "Python detected:"
python3 --version

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Run setup
echo "Running project setup..."
python3 setup.py

echo ""
echo "Installation complete!"
echo "You can now run the application:"
echo "  - Tkinter version: python3 src/tkinter_implementation.py"
echo "  - PyQt6 version: python3 src/pyqt6_implementation.py"
echo ""
echo "For development:"
echo "  - Run tests: python3 -m pytest tests/"
echo "  - Code formatting: black src/"
echo "  - Linting: flake8 src/"