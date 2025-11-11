# Vosk-based Interpreter Helper

A real-time, privacy-focused speech-to-text transcription system designed specifically for interpreter assistance. This application provides dual-language transcription with confidence scoring and professional-grade features for live interpreting scenarios.

## 🌟 Features

### Core Functionality
- **Real-time dual-language transcription** - Simultaneous English and Spanish processing
- **Confidence-based filtering** - Color-coded accuracy indicators for word-level confidence
- **Privacy-focused** - No data storage, all processing happens locally
- **Multi-platform support** - Windows, macOS, and Linux

### User Interface
- **Side-by-side language panels** - Clean, professional layout
- **Adjustable transparency** - Perfect for video calls
- **Always-on-top mode** - Keeps captions visible over other applications
- **Responsive design** - Scales with window size
- **Audio device selection** - Choose your preferred microphone

### Professional Features
- **Audio level visualization** - Real-time input monitoring
- **Sentence tracking** - Intelligent sentence boundary detection
- **History management** - Maintains transcription history (configurable limits)
- **Multiple implementations** - Choose between Tkinter (lightweight) or PyQt6 (professional)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Microphone or audio input device
- At least 1GB free disk space (for language models)

### Installation

#### Option 1: Automated Installation (Recommended)

**Windows:**
```bash
install.bat
```

**Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

#### Option 2: Manual Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd vosk-based-interpreter-helper
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run setup:**
```bash
python setup.py
```

4. **Download language models** (if not already present):
   - Download from [Vosk Models](https://alphacephei.com/vosk/models)
   - Extract to the `models/` directory
   - Current models: English, Spanish, French

### Running the Application

**Tkinter Version (Lightweight):**
```bash
python captioner.py
```

**PyQt6 Version (Professional):**
```bash
python GUI.py
```

## 📁 Project Structure

```
vosk-based-interpreter-helper/
├── src/                          # Source code
│   ├── tkinter_implementation.py # Tkinter-based GUI
│   └── pyqt6_implementation.py   # PyQt6-based GUI
├── tests/                        # Unit and integration tests
├── config/                       # Configuration files
├── scripts/                      # Utility scripts
├── docs/                         # Documentation
├── models/                       # Vosk language models
│   ├── vosk-model-small-en-us/   # English model
│   ├── vosk-model-small-es/      # Spanish model
│   └── vosk-model-small-fr/      # French model
├── requirements.txt              # Python dependencies
├── setup.py                      # Project setup script
├── install.bat                   # Windows installation script
├── install.sh                    # Linux/macOS installation script
├── README.md                     # This file
└── project_analysis_report.md    # Technical analysis
```

## 🎯 Usage Guide

### Basic Operation

1. **Start the application** using one of the implementation options
2. **Select your audio input device** from the dropdown menu
3. **Grant microphone permissions** when prompted
4. **Begin speaking** - transcription will appear in real-time
5. **Monitor confidence levels** using the color coding:
   - 🟢 **Green**: High confidence (≥85%)
   - 🟡 **Yellow**: Medium confidence (65-84%)
   - 🔴 **Red**: Low confidence (50-64%)

### Professional Features

- **Privacy Mode**: No transcriptions are saved to disk
- **Always On Top**: Keeps the application visible during video calls
- **Transparency Control**: Adjust window opacity for better integration
- **Audio Device Switching**: Change input sources on-the-fly
- **History Management**: Clear all history with one click

### Configuration

The application includes several configurable parameters:

- **Confidence Threshold**: Minimum confidence for word inclusion (default: 50%)
- **History Limit**: Maximum number of captions to store (default: 100)
- **Audio Settings**: Sample rate (16kHz), chunk size (1024 frames)
- **Font Scaling**: Automatic font sizing based on window dimensions

## 🛠️ Development

### Development Setup

1. **Install development dependencies:**
```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

2. **Run tests:**
```bash
python -m pytest tests/ -v --cov=src
```

3. **Code formatting:**
```bash
black src/
flake8 src/
```

### Testing

- **Unit Tests**: Located in `tests/unit/`
- **Integration Tests**: Located in `tests/integration/`
- **Audio Tests**: Specialized tests for audio processing functionality

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Submit a pull request

## 📊 Technical Details

### Architecture

The application uses a multi-threaded architecture:

- **Audio Thread**: Captures and processes audio input
- **Recognition Thread**: Handles speech-to-text conversion
- **UI Thread**: Manages user interface updates
- **Worker Threads**: Process results and update displays

### Dependencies

**Core Dependencies:**
- `vosk`: Speech recognition engine
- `pyaudio`: Audio I/O (Tkinter implementation)
- `sounddevice`: Audio streaming (PyQt6 implementation)
- `numpy`: Numerical processing
- `PyQt6`: Professional GUI framework

**Development Dependencies:**
- `pytest`: Testing framework
- `black`: Code formatting
- `flake8`: Linting

### Performance

- **Latency**: ~200-500ms end-to-end
- **Memory Usage**: ~200-500MB (depends on active languages)
- **CPU Usage**: ~10-30% on modern hardware
- **Accuracy**: Medium-High (uses small models for speed)

## 🔧 Configuration

### Language Models

The application supports multiple languages through Vosk models:

1. **English**: `vosk-model-small-en-us` (recommended)
2. **Spanish**: `vosk-model-small-es` (recommended)
3. **French**: `vosk-model-small-fr` (available)

To add new languages:
1. Download the model from the Vosk website
2. Extract to the `models/` directory
3. Update the language configuration in the source code

### Audio Settings

Configurable audio parameters:
- **Sample Rate**: 16000 Hz (optimized for speech)
- **Channels**: 1 (mono)
- **Chunk Size**: 1024 frames
- **Format**: 16-bit integer

## 📋 Roadmap

This project is actively developed with a comprehensive roadmap of 106 planned features across 10 categories:

### Phase 2: Code Quality & Testing
- Unit tests and integration tests
- Configuration management
- Error handling improvements
- Performance optimization

### Phase 3: User Experience Enhancement
- Enhanced GUI with settings management
- Keyboard shortcuts and hotkeys
- Mini mode for small screens
- Session profiles

### Phase 4: Advanced Features
- Technical term highlighting and translation
- Personal glossary management
- React web interface
- Cloud integration options

For the complete feature list, see `implementations list.txt`.

## 🤝 Support

### Getting Help

1. **Check the documentation** in the `docs/` directory
2. **Review existing issues** on GitHub
3. **Create a new issue** with detailed information
4. **Join discussions** in the project discussions

### Reporting Bugs

When reporting bugs, please include:
- Operating system and Python version
- Complete error messages
- Steps to reproduce the issue
- Audio device information

### Feature Requests

We welcome feature requests! Please check the existing roadmap first and provide:
- Use case description
- Proposed implementation approach
- Potential impact on existing features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Vosk Team**: For the excellent offline speech recognition engine
- **Python Community**: For the robust audio processing libraries
- **Interpreter Community**: For feedback and feature requirements

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-11  
**Status**: Production Ready (Python implementations)  

For technical questions or support, please refer to the `project_analysis_report.md` file for detailed technical information.