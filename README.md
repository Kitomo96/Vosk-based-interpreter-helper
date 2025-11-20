# Vosk-based Interpreter Helper

A real-time, privacy-focused speech-to-text transcription system designed specifically for interpreter assistance. This Electron-based application provides dual-language transcription with intelligent language detection and professional-grade features for live interpreting scenarios.

## 🌟 Features

### Core Functionality
- **Real-time dual-language transcription** - Simultaneous processing of multiple languages
- **Intelligent language detection** - Automatic detection with confidence scoring
- **Privacy-focused** - No data storage, all processing happens locally offline
- **Multi-platform support** - Windows, macOS, and Linux

### User Interface
- **Modern Electron UI** - Clean, professional React-based interface
- **Side-by-side language panels** - Clear visualization of both languages
- **Language swapping** - Easily swap left/right language displays
- **Dynamic language selection** - Choose which languages to process
- **Real-time updates** - Instant transcription display

### Professional Features
- **Offline speech recognition** - Uses Vosk models, no internet required
- **Confidence-based filtering** - Quality indicators for transcription accuracy
- **Sentence tracking** - Intelligent sentence boundary detection
- **History management** - Maintains transcription history per language

## 🚀 Quick Start

### Prerequisites
- **Node.js** 16+ (for Electron frontend)
- **Python** 3.8+ (for speech recognition backend)
- **Microphone** or audio input device
- **2GB+ free disk space** (for language models)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd vosk-based-interpreter-helper
```

2. **Install Python backend dependencies:**
```bash
pip install -r requirements.txt
```

3. **Download Vosk language models:**
   - Download from [Vosk Models](https://alphacephei.com/vosk/models)
   - Extract to the `models/` directory
   - Recommended models:
     - English: `vosk-model-small-en-us`
     - Spanish: `vosk-model-small-es`
     - French: `vosk-model-small-fr`

4. **Install Electron frontend dependencies:**
```bash
cd live-captioner
npm install
```

### Running the Application

**Development mode:**
```bash
cd live-captioner
npm run dev          # Start React dev server
npm run electron:only  # In another terminal, start Electron
```

**Production build:**
```bash
cd live-captioner
npm run build
npm run electron
```

## 📁 Project Structure

```
vosk-based-interpreter-helper/
├── src/                          # Python backend
│   ├── electron_bridge.py        # Bridge between Electron and Python
│   ├── speech_recognition_engine.py  # Vosk speech recognition
│   ├── audio_manager.py          # Audio device management
│   └── configuration_manager.py  # Configuration handling
├── live-captioner/               # Electron frontend
│   ├── public/
│   │   └── electron.js           # Electron main process
│   ├── src/
│   │   ├── App.js                # React main component
│   │   └── App.css               # Styling
│   └── package.json              # Frontend dependencies
├── config/                       # Configuration files
│   └── settings.ini              # Backend settings
├── models/                       # Vosk language models
│   ├── vosk-model-small-en-us/   # English model
│   ├── vosk-model-small-es/      # Spanish model
│   └── vosk-model-small-fr/      # French model
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🎯 Usage Guide

### Basic Operation

1. **Start the application** using the commands above
2. **Select languages** using the dropdown menus in the UI
3. **Grant microphone permissions** when prompted
4. **Begin speaking** - transcription will appear in real-time in the selected language panels

### Features

- **Language Selection**: Choose which two languages to display and process
- **Swap Languages**: Click the swap button to exchange left/right panels
- **Language Detection**: The system automatically detects which language is being spoken
- **Real-time Transcription**: See partial results as you speak, with final results confirmed

## 🛠️ Development

### Architecture

The application uses a **hybrid architecture**:

- **Frontend (Electron + React)**: Modern UI built with React, packaged with Electron
- **Backend (Python)**: Speech recognition engine using Vosk
- **Communication**: IPC (Inter-Process Communication) between Electron and Python via stdin/stdout

### Backend Components

- **`electron_bridge.py`**: Main entry point, handles IPC with Electron
- **`speech_recognition_engine.py`**: Vosk integration, language detection, transcription
- **`audio_manager.py`**: Audio device enumeration and stream management
- **`configuration_manager.py`**: INI-based configuration system

### Frontend Components

- **`electron.js`**: Electron main process, spawns Python backend
- **`App.js`**: React UI, handles user interaction and displays transcriptions
- **`App.css`**: Styling for the modern interface

### Adding New Languages

1. Download the Vosk model for your language
2. Extract to `models/` directory
3. Update `config/settings.ini` with the model path
4. Add the language code to the frontend language options in `App.js`

## 📊 Technical Details

### Dependencies

**Python Backend:**
- `vosk`: Offline speech recognition engine
- `pyaudio`: Audio I/O
- `numpy`: Numerical processing

**Electron Frontend:**
- `electron`: Desktop application framework
- `react`: UI framework
- `react-scripts`: Build tooling

### Performance

- **Latency**: ~200-500ms end-to-end
- **Memory Usage**: ~300-600MB (depends on active languages)
- **CPU Usage**: ~15-40% on modern hardware
- **Accuracy**: Medium-High (uses small models for speed)

## 🔧 Configuration

### Backend Configuration

Edit `config/settings.ini`:

```ini
[audio]
sample_rate = 16000
chunk_size = 1024

[languages]
english = models/vosk-model-small-en-us
spanish = models/vosk-model-small-es
french = models/vosk-model-small-fr

[processing]
confidence_threshold = 0.5
language_detection_threshold = 0.6
```

### Frontend Configuration

Edit `live-captioner/package.json` for Electron settings and build configuration.

## 🤝 Support

### Reporting Issues

When reporting bugs, please include:
- Operating system and version
- Python version (`python --version`)
- Node.js version (`node --version`)
- Complete error messages
- Steps to reproduce

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Vosk Team**: For the excellent offline speech recognition engine
- **Electron Team**: For the cross-platform desktop framework
- **React Team**: For the UI framework

---

**Version**: 2.0.0 (Electron Implementation)  
**Last Updated**: 2025-11-20  
**Status**: Active Development