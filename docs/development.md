# Vosk-based Interpreter Helper - Development Guide

This document contains development information and instructions for contributors.

## Development Setup

### Prerequisites
- Python 3.8+
- Git
- Microphone/audio input device
- 2GB+ free disk space

### Initial Setup
1. Clone the repository
2. Run the setup script: `python setup.py`
3. Install development dependencies: `pip install -r requirements.txt`
4. Verify installation: `python -m pytest tests/ --tb=short`

### Development Workflow

#### Running the Applications
```bash
# Tkinter implementation (lightweight)
python src/tkinter_implementation.py

# PyQt6 implementation (professional)
python src/pyqt6_implementation.py
```

#### Running Tests
```bash
# All tests
python -m pytest

# Unit tests only
python -m pytest tests/unit/

# Integration tests only
python -m pytest tests/integration/

# With coverage
python -m pytest --cov=src
```

#### Code Quality
```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking (if using type hints)
mypy src/
```

## Architecture Overview

### Core Components

#### Audio Processing
- **Audio Device Management**: Handles input device enumeration and selection
- **Audio Stream Processing**: Real-time audio capture and buffering
- **Audio Callback System**: Non-blocking audio data processing

#### Speech Recognition
- **Vosk Integration**: Offline speech recognition engine
- **Multi-language Support**: Simultaneous English and Spanish processing
- **Confidence Scoring**: Word-level confidence analysis
- **Sentence Tracking**: Intelligent sentence boundary detection

#### User Interface
- **Dual Implementation**: Tkinter (lightweight) and PyQt6 (professional)
- **Real-time Updates**: Live transcription display
- **Privacy-focused**: No data persistence
- **Responsive Design**: Adaptive layout and font scaling

### Configuration System
- **INI-based Configuration**: Human-readable config files
- **Section-based Settings**: Organized by functionality (audio, ui, processing)
- **Runtime Configuration**: Settings can be modified during execution

### Project Structure
```
src/
├── tkinter_implementation.py  # Tkinter-based GUI
├── pyqt6_implementation.py    # PyQt6-based GUI
└── __init__.py                # Package initialization

config/
├── settings.ini              # Main configuration
└── test_config.ini           # Test configuration

tests/
├── unit/                     # Unit tests
├── integration/              # Integration tests  
├── fixtures/                 # Test data
└── utils/                    # Test utilities
```

## Implementation Details

### Threading Architecture
The application uses a multi-threaded approach:

1. **Main Thread**: UI and user interaction
2. **Audio Thread**: Continuous audio capture
3. **Recognition Thread**: Speech-to-text processing
4. **Worker Thread**: Result processing and UI updates

### Memory Management
- **History Limits**: Configurable maximum caption history
- **Model Unloading**: Language models loaded/unloaded as needed
- **Resource Cleanup**: Proper thread and resource cleanup on shutdown

### Error Handling
- **Graceful Degradation**: Application continues working with reduced functionality
- **User-friendly Error Messages**: Clear, actionable error descriptions
- **Logging System**: Comprehensive error logging for debugging

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all public functions
- Write docstrings for all classes and functions
- Maximum line length: 88 characters (Black default)

### Testing Requirements
- Write unit tests for all new functionality
- Integration tests for multi-component features
- Mock external dependencies (audio devices, network)
- Minimum 80% code coverage

### Configuration
- Use the configuration system for all tunable parameters
- Document all configuration options
- Provide sensible defaults
- Allow runtime configuration changes

### Documentation
- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update this development guide for architectural changes
- Include docstrings for all public APIs

## Adding New Features

### Language Support
1. Download appropriate Vosk model
2. Extract to `models/` directory
3. Update configuration in `settings.ini`
4. Add language-specific UI elements
5. Add tests for new language support

### UI Components
1. Choose implementation target (Tkinter or PyQt6)
2. Follow existing patterns for consistency
3. Add responsive design considerations
4. Test across different screen sizes
5. Ensure accessibility compliance

### Audio Features
1. Consider cross-platform compatibility
2. Handle device enumeration gracefully
3. Provide fallback options for missing devices
4. Add appropriate error handling
5. Test with various audio configurations

## Debugging

### Common Issues
1. **Audio Device Not Found**: Check device permissions and drivers
2. **High CPU Usage**: Optimize audio chunk sizes and processing intervals
3. **Memory Leaks**: Check thread cleanup and model management
4. **UI Freezes**: Ensure UI updates happen in main thread

### Debug Tools
- Built-in logging system (configurable levels)
- Audio level visualization
- Performance monitoring
- Thread state inspection

### Debug Configuration
Enable debug logging in `config/settings.ini`:
```ini
[logging]
log_level = DEBUG
log_to_file = true
```

## Performance Optimization

### Areas to Monitor
- **Audio Latency**: Target <500ms end-to-end
- **Memory Usage**: Monitor model and history memory consumption
- **CPU Usage**: Keep audio processing under 30% on modern hardware
- **UI Responsiveness**: Ensure smooth real-time updates

### Optimization Techniques
- **Audio Buffering**: Balance latency vs. stability
- **Model Loading**: Lazy load models only when needed
- **UI Updates**: Batch UI updates to reduce redraw overhead
- **Thread Management**: Minimize thread contention

## Security Considerations

### Privacy
- No persistent data storage by default
- All processing happens locally
- No network communication for core functionality
- Optional logging with user consent

### Audio Permissions
- Request microphone access appropriately
- Provide clear privacy information
- Allow users to disable audio input
- Handle permission denial gracefully

## Future Development

See `project_analysis_report.md` for the complete roadmap including:
- Phase 2: Code Quality & Testing
- Phase 3: User Experience Enhancement  
- Phase 4: Advanced Features & Polish

## Getting Help

1. Check existing documentation in `docs/`
2. Review existing issues and discussions
3. Ask questions in project discussions
4. Create detailed bug reports with reproduction steps

---

*Last Updated: 2025-11-11*  
*Version: 1.0.0*