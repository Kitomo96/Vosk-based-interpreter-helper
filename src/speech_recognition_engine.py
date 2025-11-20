"""
Speech Recognition Engine for Vosk-based Interpreter Helper
Handles all Vosk model loading, speech recognition, and result processing
"""

import vosk
import json
import logging
import os
import time
import sys
from typing import Dict, List, Optional, Any, Callable, Tuple
from threading import Thread, Event
import queue

class RecognitionResult:
    """Holds the result of speech recognition"""
    
    def __init__(self, text: str, is_final: bool, confidence_scores: List[float] = None,
                 language: str = "unknown", timestamp: float = None):
        self.text = text
        self.is_final = is_final
        self.confidence_scores = confidence_scores or []
        self.language = language
        self.timestamp = timestamp or time.time()
    
    def __str__(self):
        status = "FINAL" if self.is_final else "PARTIAL"
        return f"RecognitionResult({self.language}, {status}): {self.text}"

class SpeechRecognitionEngine:
    """
    Manages speech recognition using Vosk models
    """
    
    def __init__(self, config_manager, result_callback: Optional[Callable] = None):
        self.config_manager = config_manager
        self.language_config = config_manager.get_language_config()
        self.processing_config = config_manager.get_processing_config()
        self.result_callback = result_callback
        self.logger = logging.getLogger(__name__)
        
        # Recognition components
        self.models = {}
        self.recognizers = {}
        
        # Threading
        self.processing_thread = None
        self.stop_event = Event()
        self.result_queue = queue.Queue()
        
        # State tracking
        self.current_sentences = {}
        self.current_confidences = {}
        self.word_count = {}
        
        # Active languages - which ones to process (default: en, es)
        self.active_languages = set(['en', 'es'])
        
        # Initialize speech recognition
        self._initialize_recognition_system()
    
    def _initialize_recognition_system(self) -> None:
        """Initialize speech recognition models and recognizers"""
        try:
            self._load_language_models()
            self._initialize_recognizers()
            self.logger.info("Speech recognition system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {e}")
            raise
    
    def _load_language_models(self) -> None:
        """Load Vosk models for supported languages"""
        language_mapping = {
            'en': 'english',
            'es': 'spanish',
            'fr': 'french'
        }
        
        for lang_code, config_key in language_mapping.items():
            model_path = self.language_config.get(config_key)
            
            # Handle path resolution when running from src/ directory
            if not os.path.isabs(model_path):
                # Try current directory first
                if os.path.exists(model_path):
                    pass  # Use as-is
                else:
                    # Try relative to src/ directory
                    src_relative_path = f"../{model_path}"
                    if os.path.exists(src_relative_path):
                        model_path = src_relative_path
                    else:
                        # Try relative to project root
                        project_root_path = f"../../{model_path}"
                        if os.path.exists(project_root_path):
                            model_path = project_root_path
            
            if model_path and os.path.exists(model_path):
                try:
                    model = vosk.Model(model_path)
                    self.models[lang_code] = model
                    self.logger.info(f"Loaded {lang_code} model from {model_path}")
                except Exception as e:
                    self.logger.error(f"Failed to load {lang_code} model from {model_path}: {e}")
            else:
                self.logger.warning(f"Model path not found for {lang_code}: {model_path}")
        
        if not self.models:
            raise Exception("No speech recognition models could be loaded")
    
    def _initialize_recognizers(self) -> None:
        """Initialize Vosk recognizers for each language"""
        sample_rate = self.config_manager.get_audio_config()['sample_rate']
        
        for lang_code, model in self.models.items():
            try:
                recognizer = vosk.KaldiRecognizer(model, sample_rate)
                recognizer.SetWords(self.processing_config.get('enable_word_timestamps', True))
                
                self.recognizers[lang_code] = recognizer
                
                # Initialize sentence tracking
                self.current_sentences[lang_code] = ""
                self.current_confidences[lang_code] = []
                self.word_count[lang_code] = 0
                
                self.logger.info(f"Initialized recognizer for {lang_code}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize recognizer for {lang_code}: {e}")
        
        if not self.recognizers:
            raise Exception("No recognizers could be initialized")
    
    def start_recognition(self, audio_manager) -> bool:
        """Start the speech recognition processing"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.logger.warning("Speech recognition already running")
            return True
        
        self.stop_event.clear()
        self.processing_thread = Thread(target=self._recognition_loop, args=(audio_manager,))
        self.processing_thread.start()
        
        self.logger.info("Speech recognition started")
        return True
    
    def stop_recognition(self) -> None:
        """Stop speech recognition processing"""
        if self.processing_thread:
            self.stop_event.set()
            self.processing_thread.join(timeout=2.0)
            
            if self.processing_thread.is_alive():
                self.logger.warning("Speech recognition thread did not stop cleanly")
            
            self.processing_thread = None
        
        self.logger.info("Speech recognition stopped")
    
    def _recognition_loop(self, audio_manager) -> None:
        """Main recognition processing loop"""
        
        while not self.stop_event.is_set():
            try:
                # Get audio data
                audio_data = audio_manager.get_audio_data(timeout=0.1)
                if not audio_data:
                    continue
                
                # Determine which languages to process based on active languages
                languages_to_process = [l for l in self.active_languages if l in self.recognizers]
                
                # Fallback: If no active languages are selected for processing
                # default to processing all available recognizers to ensure responsiveness
                if not languages_to_process:
                     languages_to_process = list(self.recognizers.keys())
                
                # Process audio for selected languages
                for lang_code in languages_to_process:
                    self._process_audio_for_language(audio_data, lang_code, self.recognizers[lang_code])
                
            except Exception as e:
                self.logger.error(f"Error in recognition loop: {e}")
    
    def _process_audio_for_language(self, audio_data: bytes, lang_code: str, recognizer) -> None:
        """Process audio data for a specific language"""
        try:
            # Check for final results
            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                
                if text:
                    # CRITICAL FIX: Use ONLY the final result text (don't combine with current sentence)
                    # The final result already contains the complete accumulated sentence
                    final_text = text
                    final_confidences = [word.get('conf', 0.0) for word in result.get('result', [])]
                    
                    # Create final result
                    recognition_result = RecognitionResult(
                        text=final_text,
                        is_final=True,
                        confidence_scores=final_confidences,
                        language=lang_code
                    )
                    
                    # Reset sentence tracking
                    self.current_sentences[lang_code] = ""
                    self.current_confidences[lang_code] = []
                    self.word_count[lang_code] = 0
                    
                    # Notify callback
                    self._notify_result(recognition_result)
            
            # Process partial results
            partial = json.loads(recognizer.PartialResult())
            partial_text = partial.get("partial", "").strip()
            
            if partial_text:
                words = partial_text.split()
                word_confidences = [word.get('conf', 0.0) for word in partial.get('result', [])]
                
                if len(words) <= self.processing_config.get('initial_finalization_threshold', 4):
                    # Show "..." for short partial results
                    recognition_result = RecognitionResult(
                        text="...",
                        is_final=False,
                        language=lang_code
                    )
                    self._notify_result(recognition_result)
                else:
                    # Update current sentence
                    if partial_text.startswith(self.current_sentences[lang_code]):
                        # Additional text
                        additional_text = partial_text[len(self.current_sentences[lang_code]):].strip()
                        self.current_sentences[lang_code] = partial_text
                        self.current_confidences[lang_code] = word_confidences
                        self.word_count[lang_code] = len(words)
                    else:
                        # New sentence
                        self.current_sentences[lang_code] = partial_text
                        self.current_confidences[lang_code] = word_confidences
                        self.word_count[lang_code] = len(words)
                    
                    # Show current sentence
                    recognition_result = RecognitionResult(
                        text=self.current_sentences[lang_code],
                        is_final=False,
                        confidence_scores=self.current_confidences[lang_code],
                        language=lang_code
                    )
                    self._notify_result(recognition_result)
        
        except Exception as e:
            self.logger.error(f"Error processing audio for {lang_code}: {e}")
    
    def _notify_result(self, result: RecognitionResult) -> None:
        """Notify result callback or queue the result"""
        if self.result_callback:
            try:
                self.result_callback(result)
            except Exception as e:
                self.logger.error(f"Error in result callback: {e}")
        else:
            try:
                self.result_queue.put(result, timeout=0.1)
            except queue.Full:
                pass  # Drop result if queue is full
    
    def get_queued_result(self, timeout: float = 0.0) -> Optional[RecognitionResult]:
        """Get a result from the queue"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def reset_recognition(self, language: Optional[str] = None) -> None:
        """Reset recognition state for specific language or all languages"""
        if language:
            if language in self.recognizers:
                self.current_sentences[language] = ""
                self.current_confidences[language] = []
                self.word_count[language] = 0
        else:
            # Reset all languages
            for lang_code in self.recognizers:
                self.current_sentences[lang_code] = ""
                self.current_confidences[lang_code] = []
                self.word_count[lang_code] = 0
        
        self.logger.info(f"Recognition reset for language: {language or 'all'}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return list(self.recognizers.keys())
    
    def get_language_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get recognition statistics for each language"""
        stats = {}
        for lang_code in self.recognizers:
            stats[lang_code] = {
                'current_word_count': self.word_count[lang_code],
                'has_active_sentence': len(self.current_sentences[lang_code]) > 0,
                'model_loaded': lang_code in self.models,
                'recognizer_active': lang_code in self.recognizers
            }
        return stats
    
    def test_model_loading(self) -> Dict[str, bool]:
        """Test if all language models can be loaded"""
        results = {}
        language_mapping = {
            'english': 'en',
            'spanish': 'es',
            'french': 'fr'
        }
        
        for config_key, lang_code in language_mapping.items():
            model_path = self.language_config.get(config_key)
            
            # Handle path resolution (same logic as in _load_language_models)
            if not os.path.isabs(model_path):
                # Try current directory first
                if os.path.exists(model_path):
                    pass  # Use as-is
                else:
                    # Try relative to src/ directory
                    src_relative_path = f"../{model_path}"
                    if os.path.exists(src_relative_path):
                        model_path = src_relative_path
                    else:
                        # Try relative to project root
                        project_root_path = f"../../{model_path}"
                        if os.path.exists(project_root_path):
                            model_path = project_root_path
            
            try:
                if model_path and os.path.exists(model_path):
                    model = vosk.Model(model_path)
                    results[lang_code] = True
                    del model  # Clean up
                else:
                    results[lang_code] = False
            except Exception as e:
                self.logger.error(f"Model test failed for {lang_code}: {e}")
                results[lang_code] = False
        return results
    
    def set_active_languages(self, languages: List[str]) -> None:
        """Update the list of active languages to process"""
        import sys
        sys.stderr.write(f"DEBUG: set_active_languages called with: {languages}\n")
        sys.stderr.flush()
        try:
            # Filter to only supported languages
            valid_languages = [l for l in languages if l in self.models]
            sys.stderr.write(f"DEBUG: valid_languages: {valid_languages}\n")
            sys.stderr.flush()
            
            if valid_languages:
                self.active_languages = set(valid_languages)
                self.logger.info(f"Active languages updated to: {self.active_languages}")
                sys.stderr.write(f"DEBUG: Active languages updated to: {self.active_languages}\n")
                sys.stderr.flush()
            else:
                self.logger.warning(f"No valid languages provided in: {languages}")
                sys.stderr.write(f"DEBUG: No valid languages found. Models loaded: {list(self.models.keys())}\n")
                sys.stderr.flush()
        except Exception as e:
            self.logger.error(f"Error setting active languages: {e}")
            sys.stderr.write(f"DEBUG: Error setting active languages: {e}\n")
            sys.stderr.flush()

    def shutdown(self) -> None:
        """Shutdown the speech recognition engine"""
        self.logger.info("Shutting down speech recognition engine")
        
        self.stop_recognition()
        
        # Clear data structures
        self.models.clear()
        self.recognizers.clear()
        self.current_sentences.clear()
        self.current_confidences.clear()
        self.word_count.clear()
        
        # Clear result queue
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break
        
        self.logger.info("Speech recognition engine shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'processing_thread') and self.processing_thread and self.processing_thread.is_alive():
            self.shutdown()