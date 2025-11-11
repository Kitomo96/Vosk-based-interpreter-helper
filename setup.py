#!/usr/bin/env python3
"""
Project setup script for Vosk-based Interpreter Helper
This script helps set up the development environment
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"OK: Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    
    # Check if pip is available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("ERROR: pip is not available. Please install pip first.")
        sys.exit(1)
    
    # Install dependencies
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("OK: Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        "src",
        "tests", 
        "config",
        "scripts",
        "docs",
        "models"
    ]
    
    print("Creating project directories...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  OK: {directory}/")

def setup_models():
    """Set up Vosk language models"""
    models_dir = "models"
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        
    # Check if models already exist
    existing_models = [d for d in os.listdir(models_dir) if d.startswith("vosk-model")]
    if existing_models:
        print(f"INFO: Found {len(existing_models)} existing language models")
        for model in existing_models:
            print(f"  ✅ {model}")
    else:
        print("WARNING: No Vosk models found. You may need to download them.")
        print("   Models can be downloaded from: https://alphacephei.com/vosk/models")

def check_system_dependencies():
    """Check for system-specific dependencies"""
    system = platform.system()
    
    print(f"INFO: Detected system: {system}")
    
    if system == "Linux":
        print("INFO: Linux dependencies you may need:")
        print("   - PortAudio development headers: sudo apt-get install portaudio19-dev")
        print("   - ALSA development headers: sudo apt-get install libasound2-dev")
    elif system == "Darwin":  # macOS
        print("INFO: macOS dependencies:")
        print("   - Xcode command line tools: xcode-select --install")
        print("   - PortAudio: brew install portaudio")
    elif system == "Windows":
        print("INFO: Windows dependencies:")
        print("   - Visual C++ Redistributable (usually pre-installed)")

def main():
    """Main setup function"""
    print("=== Vosk-based Interpreter Helper Setup ===")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create project structure
    create_directories()
    
    # Check system dependencies
    check_system_dependencies()
    
    # Install Python dependencies
    install_dependencies()
    
    # Setup models
    setup_models()
    
    print("\nSUCCESS: Setup complete!")
    print("\nNext steps:")
    print("1. Test the Tkinter implementation: python src/tkinter_implementation.py")
    print("2. Test the PyQt6 implementation: python src/pyqt6_implementation.py")
    print("3. Run tests: python -m pytest tests/")
    print("4. Check documentation in docs/")
    
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()