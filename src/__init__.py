# Vosk-based Interpreter Helper - Version Information
VERSION = "1.0.0"
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable"
}

# Development metadata
__version__ = VERSION
__author__ = "Vosk Interpreter Helper Team"
__email__ = "support@vosk-interpreter-helper.org"
__description__ = "Real-time, privacy-focused speech-to-text transcription system for interpreter assistance"

# Build information
BUILD_DATE = "2025-11-11"
PYTHON_MIN_VERSION = (3, 8)
SUPPORTED_PLATFORMS = ["Windows", "Linux", "macOS"]

# Dependencies version requirements
DEPENDENCIES = {
    "vosk": ">=0.3.45",
    "pyaudio": ">=0.2.11", 
    "sounddevice": ">=0.4.6",
    "PyQt6": ">=6.5.0",
    "numpy": ">=1.24.0"
}

# Configuration
DEFAULT_CONFIG_FILE = "config/settings.ini"
DEFAULT_TEST_CONFIG = "config/test_config.ini"