"""
LiveCaptioner - Main Application Orchestrator
Refactored, modular implementation of the Vosk-based Interpreter Helper
"""

import logging
import sys
import threading
import time
import signal
from typing import Optional

# Import our modular components
from configuration_manager import ConfigurationManager
from audio_manager import AudioManager
from speech_recognition_engine import SpeechRecognitionEngine, RecognitionResult
from caption_processor import CaptionProcessor
from ui_manager import UIManager

class LiveCaptioner:
    """
    Main application orchestrator that coordinates all subsystems
    """
    
    def __init__(self, config_file: str = "../config/settings.ini"):
        # Initialize configuration first
        self.config_manager = ConfigurationManager(config_file)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Component state
        self.audio_manager = None
        self.speech_engine = None
        self.caption_processor = None
        self.ui_manager = None
        
        # Application state
        self.is_initialized = False
        self.is_running = False
        self.shutdown_requested = False
        
        # Threading
        self.ui_thread = None
        
        # UI update flags - for event-driven updates only
        self.pending_ui_updates = {'en': False, 'es': False}
        self.ui_update_needed = False
        
        # Initialize components
        self._initialize_components()
    
    def _setup_logging(self) -> None:
        """Setup application logging"""
        log_config = self.config_manager.get_logging_config()
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config.get('log_level', 'INFO').upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        
        # File logging if enabled
        if log_config.get('log_to_file', False):
            file_handler = logging.FileHandler(log_config.get('log_file_path', 'logs/app.log'))
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(file_handler)
    
    def _initialize_components(self) -> bool:
        """Initialize all application components"""
        try:
            self.logger.info("Initializing LiveCaptioner components...")
            
            # Initialize caption processor
            self.caption_processor = CaptionProcessor(self.config_manager)
            self.logger.info("✓ Caption processor initialized")
            
            # Initialize audio manager
            self.audio_manager = AudioManager(self.config_manager)
            self.logger.info("✓ Audio manager initialized")
            
            # Initialize speech recognition engine
            self.speech_engine = SpeechRecognitionEngine(
                self.config_manager,
                result_callback=self._on_recognition_result
            )
            self.logger.info("✓ Speech recognition engine initialized")
            
            # Initialize UI manager
            self.ui_manager = UIManager(self.config_manager, self.caption_processor)
            
            # Setup UI callbacks
            self._setup_ui_callbacks()
            
            self.logger.info("✓ UI manager initialized")
            
            self.is_initialized = True
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def _setup_ui_callbacks(self) -> None:
        """Setup callbacks between UI and other components"""
        # Audio device change callback
        self.ui_manager.set_device_change_callback(self._on_device_change)
        
        # Clear history callback
        self.ui_manager.set_clear_history_callback(self._on_clear_history)
        
        # Window close callback
        self.ui_manager.set_window_close_callback(self._on_window_close)
        
        # Language detection callbacks
        self.ui_manager.set_language_callbacks(
            override_callback=self._on_language_override,
            reset_callback=self._on_language_reset
        )
    
    def start_application(self) -> bool:
        """Start the complete application"""
        if not self.is_initialized:
            self.logger.error("Application not properly initialized")
            return False
        
        if self.is_running:
            self.logger.warning("Application already running")
            return True
        
        try:
            self.logger.info("Starting LiveCaptioner application...")
            
            # Start audio manager
            if not self.audio_manager.start_stream():
                self.logger.error("Failed to start audio stream")
                return False
            
            # Start speech recognition
            if not self.speech_engine.start_recognition(self.audio_manager):
                self.logger.error("Failed to start speech recognition")
                return False
            
            # Update UI with available devices
            devices = self.audio_manager.get_devices_info()
            self.ui_manager.update_audio_devices(devices)
            
            # Update status
            self.ui_manager.update_status("Active", 'green')
            
            self.is_running = True
            self.shutdown_requested = False
            
            self.logger.info("LiveCaptioner application started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start application: {e}")
            return False
    
    def stop_application(self) -> None:
        """Stop the application gracefully"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping LiveCaptioner application...")
        
        self.shutdown_requested = True
        
        # Stop speech recognition
        if self.speech_engine:
            self.speech_engine.stop_recognition()
        
        # Stop audio stream
        if self.audio_manager:
            self.audio_manager.stop_stream()
        
        self.is_running = False
        
        self.logger.info("LiveCaptioner application stopped")
    
    def run_application(self) -> None:
        """Run the application (blocking call)"""
        if not self.is_initialized:
            self.logger.error("Cannot run uninitialized application")
            return
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start application components
            if not self.start_application():
                self.logger.error("Failed to start application")
                return
            
            # Initialize UI
            if not self.ui_manager.initialize_ui():
                self.logger.error("Failed to initialize UI")
                return
            
            # Start UI main loop (NO PROCESSING THREAD NEEDED - event-driven updates)
            self.ui_manager.start_mainloop()
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self._cleanup()
    
    def _schedule_ui_update(self, language: str) -> None:
        """Schedule UI update for a specific language (event-driven approach)"""
        self.pending_ui_updates[language] = True
        
        # Schedule UI update on the main thread
        if self.ui_manager and self.ui_manager.is_ui_running():
            self.ui_manager.get_window().after(0, self._perform_ui_update)
    
    def _perform_ui_update(self) -> None:
        """Perform pending UI updates"""
        if not self.ui_manager or not self.ui_manager.is_ui_running():
            return
            
        for language in ['en', 'es']:
            if self.pending_ui_updates[language]:
                self.ui_manager.update_captions(language)
                self.pending_ui_updates[language] = False
    
    def _request_ui_update_all(self) -> None:
        """Request UI update for all languages"""
        for language in ['en', 'es']:
            self.pending_ui_updates[language] = True
        
        if self.ui_manager and self.ui_manager.is_ui_running():
            self.ui_manager.get_window().after(0, self._perform_ui_update)
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}")
        self.shutdown_requested = True
        self.ui_manager.stop_mainloop()
    
    def _on_recognition_result(self, result: RecognitionResult) -> None:
        """Handle recognition results from speech engine"""
        try:
            # Process the result through caption processor
            caption_entry = self.caption_processor.process_recognition_result(
                text=result.text,
                is_final=result.is_final,
                language=result.language,
                confidence_scores=result.confidence_scores
            )
            
            # Schedule UI update for the specific language (event-driven)
            self._schedule_ui_update(result.language)
            
            # Update language detection indicator for final results
            if result.is_final and result.text.strip():
                # Get current language detection from speech engine
                detected_lang, confidence = self.speech_engine.get_detected_language()
                self.ui_manager.update_language_detection(detected_lang, confidence)
                self.ui_manager.show_visual_feedback()
                
                # Update detection statistics panel if available
                detection_stats = self.speech_engine.get_language_detection_stats()
                self.ui_manager.show_language_detection_panel(detection_stats)
            
        except Exception as e:
            self.logger.error(f"Error processing recognition result: {e}")
    
    def _on_device_change(self, device_name: str) -> None:
        """Handle audio device change from UI"""
        try:
            # Find device index by name
            devices = self.audio_manager.get_devices_info()
            device_index = None
            
            for device in devices:
                if device['name'] == device_name:
                    device_index = device['index']
                    break
            
            if device_index is not None:
                success = self.audio_manager.set_device(device_index)
                if success:
                    self.ui_manager.update_status(f"🎤 Active - {device_name}", 'green')
                    self.logger.info(f"Switched to audio device: {device_name}")
                else:
                    self.ui_manager.update_status("❌ Error: Could not switch device", 'red')
                    self.logger.error(f"Failed to switch to device: {device_name}")
            else:
                self.logger.error(f"Device not found: {device_name}")
                
        except Exception as e:
            self.logger.error(f"Error handling device change: {e}")
            self.ui_manager.update_status("❌ Error: Device change failed", 'red')
    
    def _on_clear_history(self) -> None:
        """Handle clear history request from UI"""
        try:
            # Clear all language histories
            self.caption_processor.clear_history()
            
            # Request UI update for all languages (event-driven)
            self._request_ui_update_all()
            
            self.ui_manager.update_status("🗑️ History cleared", 'yellow')
            self.logger.info("Caption history cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing history: {e}")
    
    def _on_window_close(self) -> None:
        """Handle window close event"""
        self.logger.info("Window close requested")
        self.shutdown_requested = True
        self.ui_manager.stop_mainloop()
    
    def _on_language_override(self, language: str) -> None:
        """Handle manual language override from UI"""
        try:
            success = self.speech_engine.force_language_detection(language)
            if success:
                self.ui_manager.update_status(f"Language manually set to {language.upper()}", 'blue')
                self.logger.info(f"Language detection manually set to: {language}")
            else:
                self.ui_manager.update_status("Error: Invalid language selection", 'red')
                self.logger.error(f"Invalid language selection: {language}")
        except Exception as e:
            self.logger.error(f"Error handling language override: {e}")
            self.ui_manager.update_status("Error: Language override failed", 'red')
    
    def _on_language_reset(self) -> None:
        """Handle language detection reset to automatic mode"""
        try:
            self.speech_engine.reset_language_detection()
            self.ui_manager.update_status("Language detection reset to automatic", 'blue')
            self.logger.info("Language detection reset to automatic mode")
        except Exception as e:
            self.logger.error(f"Error resetting language detection: {e}")
            self.ui_manager.update_status("Error: Language reset failed", 'red')
    
    def _cleanup(self) -> None:
        """Cleanup all resources"""
        self.logger.info("Cleaning up resources...")
        
        # Stop application if running
        if self.is_running:
            self.stop_application()
        
        # Wait for processing thread to finish (removed - no longer needed)
        # if self.processing_thread and self.processing_thread.is_alive():
        #     self.processing_thread.join(timeout=2.0)
        
        # Shutdown components
        components = [
            ('UI Manager', self.ui_manager),
            ('Speech Engine', self.speech_engine),
            ('Audio Manager', self.audio_manager),
            ('Caption Processor', self.caption_processor)
        ]
        
        for name, component in components:
            if component:
                try:
                    component.shutdown()
                    self.logger.info(f"{name} shutdown complete")
                except Exception as e:
                    self.logger.error(f"Error shutting down {name}: {e}")
        
        self.logger.info("Cleanup complete")
    
    def _cleanup(self) -> None:
        """Cleanup all resources"""
        self.logger.info("Cleaning up resources...")
        
        # Stop application if running
        if self.is_running:
            self.stop_application()
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        # Shutdown components
        components = [
            ('UI Manager', self.ui_manager),
            ('Speech Engine', self.speech_engine),
            ('Audio Manager', self.audio_manager),
            ('Caption Processor', self.caption_processor)
        ]
        
        for name, component in components:
            if component:
                try:
                    component.shutdown()
                    self.logger.info(f"{name} shutdown complete")
                except Exception as e:
                    self.logger.error(f"Error shutting down {name}: {e}")
        
        self.logger.info("Cleanup complete")
    
    def get_status_info(self) -> dict:
        """Get current application status information"""
        audio_device = self.audio_manager.get_current_device_info() if self.audio_manager else None
        speech_stats = self.speech_engine.get_language_stats() if self.speech_engine else {}
        processing_stats = self.caption_processor.get_processing_stats() if self.caption_processor else {}
        
        return {
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'audio_device': audio_device,
            'speech_recognition_stats': speech_stats,
            'caption_processing_stats': processing_stats,
            'supported_languages': list(speech_stats.keys()) if speech_stats else []
        }
    
    def test_all_components(self) -> dict:
        """Test all components and return test results"""
        results = {}
        
        try:
            # Test configuration
            results['configuration'] = True
            
            # Test audio manager
            if self.audio_manager:
                results['audio_manager'] = self.audio_manager.available_devices is not None
            else:
                results['audio_manager'] = False
            
            # Test speech recognition models
            if self.speech_engine:
                model_tests = self.speech_engine.test_model_loading()
                results['speech_models'] = all(model_tests.values())
                results['model_details'] = model_tests
            else:
                results['speech_models'] = False
            
            # Test UI initialization
            if self.ui_manager:
                results['ui_manager'] = True
            else:
                results['ui_manager'] = False
            
            # Test caption processor
            if self.caption_processor:
                results['caption_processor'] = True
            else:
                results['caption_processor'] = False
            
            results['overall_success'] = all(
                v for k, v in results.items()
                if k not in ['model_details', 'overall_success']
            )
            
        except Exception as e:
            results['error'] = str(e)
            results['overall_success'] = False
        
        return results
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'is_running') and self.is_running:
            self._cleanup()

def main():
    """Main entry point for the application"""
    print("Starting Vosk-based Interpreter Helper (Modular Version - Event-Driven UI)...")
    
    try:
        # Create and run application
        app = LiveCaptioner()
        
        # Test components
        test_results = app.test_all_components()
        print(f"Component tests: {'PASSED' if test_results.get('overall_success') else 'FAILED'}")
        
        if not test_results.get('overall_success'):
            print("Component test details:")
            for component, status in test_results.items():
                if component not in ['overall_success', 'model_details']:
                    status_icon = "OK" if status else "FAIL"
                    print(f"  {status_icon} {component}")
        
        # Run the application
        app.run_application()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()