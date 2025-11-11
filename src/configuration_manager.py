"""
Configuration Manager for Vosk-based Interpreter Helper
Handles all configuration loading, validation, and management
"""

import configparser
import os
from typing import Dict, Any, Optional
import logging

class ConfigurationManager:
    """
    Manages all application configuration settings
    """
    
    def __init__(self, config_file: str = "config/settings.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger(__name__)
        self.load_configuration()
    
    def load_configuration(self) -> bool:
        """Load configuration from INI file"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return True
            else:
                self.logger.warning(f"Configuration file not found: {self.config_file}")
                self._create_default_config()
                return False
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._create_default_config()
            return False
    
    def _create_default_config(self) -> None:
        """Create default configuration structure"""
        self.config['audio'] = {
            'sample_rate': '16000',
            'channels': '1',
            'chunk_size': '1024',
            'confidence_threshold': '0.5'
        }
        
        self.config['ui'] = {
            'default_window_width': '1200',
            'default_window_height': '800',
            'font_size': '12',
            'min_font_size': '10',
            'max_font_size': '16',
            'history_limit': '100'
        }
        
        self.config['processing'] = {
            'initial_finalization_threshold': '4',
            'long_sentence_threshold': '10',
            'enable_word_timestamps': 'true'
        }
        
        self.config['languages'] = {
            'english_model': 'models/vosk-model-small-en-us',
            'spanish_model': 'models/vosk-model-small-es',
            'french_model': 'models/vosk-model-small-fr'
        }
        
        self.config['privacy'] = {
            'auto_clear_history': 'false',
            'max_history_age_hours': '24',
            'enable_private_mode': 'true'
        }
        
        self.config['logging'] = {
            'log_level': 'INFO',
            'log_to_file': 'false',
            'log_file_path': 'logs/app.log',
            'max_log_size_mb': '10'
        }
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get configuration value"""
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        return self.config.getint(section, key, fallback=fallback)
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        return self.config.getfloat(section, key, fallback=fallback)
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)
    
    def save_configuration(self) -> bool:
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration"""
        return {
            'sample_rate': self.get_int('audio', 'sample_rate', 16000),
            'channels': self.get_int('audio', 'channels', 1),
            'chunk_size': self.get_int('audio', 'chunk_size', 1024),
            'confidence_threshold': self.get_float('audio', 'confidence_threshold', 0.5)
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return {
            'default_window_width': self.get_int('ui', 'default_window_width', 1200),
            'default_window_height': self.get_int('ui', 'default_window_height', 800),
            'font_size': self.get_int('ui', 'font_size', 12),
            'min_font_size': self.get_int('ui', 'min_font_size', 10),
            'max_font_size': self.get_int('ui', 'max_font_size', 16),
            'history_limit': self.get_int('ui', 'history_limit', 100)
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return {
            'initial_finalization_threshold': self.get_int('processing', 'initial_finalization_threshold', 4),
            'long_sentence_threshold': self.get_int('processing', 'long_sentence_threshold', 10),
            'enable_word_timestamps': self.get_bool('processing', 'enable_word_timestamps', True)
        }
    
    def get_language_config(self) -> Dict[str, str]:
        """Get language model configuration"""
        return {
            'english': self.get('languages', 'english_model', 'models/vosk-model-small-en-us'),
            'spanish': self.get('languages', 'spanish_model', 'models/vosk-model-small-es'),
            'french': self.get('languages', 'french_model', 'models/vosk-model-small-fr')
        }
    
    def get_privacy_config(self) -> Dict[str, Any]:
        """Get privacy configuration"""
        return {
            'auto_clear_history': self.get_bool('privacy', 'auto_clear_history', False),
            'max_history_age_hours': self.get_int('privacy', 'max_history_age_hours', 24),
            'enable_private_mode': self.get_bool('privacy', 'enable_private_mode', True)
        }
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'log_level': self.get('logging', 'log_level', 'INFO'),
            'log_to_file': self.get_bool('logging', 'log_to_file', False),
            'log_file_path': self.get('logging', 'log_file_path', 'logs/app.log'),
            'max_log_size_mb': self.get_int('logging', 'max_log_size_mb', 10)
        }