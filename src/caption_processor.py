"""
Caption Processor for Vosk-based Interpreter Helper
Handles caption filtering, confidence scoring, and text processing
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import deque
import threading

class CaptionEntry:
    """Represents a single caption entry"""
    
    def __init__(self, text: str, confidence_scores: List[float] = None, 
                 language: str = "unknown", timestamp: float = None, is_final: bool = True):
        self.text = text
        self.confidence_scores = confidence_scores or []
        self.language = language
        self.timestamp = timestamp or time.time()
        self.is_final = is_final
        self.filtered_text = ""
        self.filtered_confidences = []
    
    def __str__(self):
        status = "FINAL" if self.is_final else "PARTIAL"
        return f"CaptionEntry({self.language}, {status}): {self.text}"

class CaptionProcessor:
    """
    Processes recognition results, filters low-confidence words, and manages caption history
    """
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.ui_config = config_manager.get_ui_config()
        self.processing_config = config_manager.get_processing_config()
        self.logger = logging.getLogger(__name__)
        
        # Caption storage
        self.caption_history = {
            'en': deque(maxlen=self.ui_config['history_limit']),
            'es': deque(maxlen=self.ui_config['history_limit']),
            'fr': deque(maxlen=self.ui_config['history_limit'])
        }
        
        # Current preview state
        self.current_previews = {
            'en': None,
            'es': None,
            'fr': None
        }
        
        # Processing state
        self.confidence_threshold = self.config_manager.get_float('audio', 'confidence_threshold', 0.5)
        self.max_history = self.ui_config['history_limit']
        
        # Threading
        self.lock = threading.Lock()
        
        self.logger.info("Caption processor initialized")
    
    def process_recognition_result(self, text: str, is_final: bool, language: str, 
                                 confidence_scores: List[float] = None) -> Optional[CaptionEntry]:
        """
        Process a recognition result and return a caption entry
        
        Args:
            text: Recognition text
            is_final: Whether this is a final result
            language: Language code (en, es, fr)
            confidence_scores: List of confidence scores for each word
        
        Returns:
            CaptionEntry object with processed caption
        """
        if not text or not language:
            return None
        
        # Validate language
        if language not in self.caption_history:
            self.logger.warning(f"Unknown language: {language}")
            return None
        
        # Create caption entry
        caption_entry = CaptionEntry(
            text=text,
            is_final=is_final,
            language=language,
            confidence_scores=confidence_scores or []
        )
        
        # Filter low confidence words if final result
        if is_final:
            filtered_text, filtered_confidences = self._filter_low_confidence_words(
                text, caption_entry.confidence_scores
            )
            caption_entry.filtered_text = filtered_text
            caption_entry.filtered_confidences = filtered_confidences
            
            # Add to history
            with self.lock:
                if caption_entry.filtered_text.strip():  # Only add non-empty captions
                    self.caption_history[language].append(caption_entry)
        else:
            # For preview, just set the filtered version
            caption_entry.filtered_text = text
            caption_entry.filtered_confidences = confidence_scores or []
        
        # Update current preview
        with self.lock:
            if is_final:
                self.current_previews[language] = None
            else:
                self.current_previews[language] = caption_entry
        
        return caption_entry
    
    def _filter_low_confidence_words(self, text: str, confidence_scores: List[float]) -> Tuple[str, List[float]]:
        """
        Filter out words with confidence below threshold
        
        Args:
            text: Original text
            confidence_scores: List of confidence scores
        
        Returns:
            Tuple of (filtered_text, filtered_confidences)
        """
        if not confidence_scores or len(confidence_scores) == 0:
            return text, confidence_scores
        
        words = text.split()
        
        # Ensure we have the same number of words and confidence scores
        if len(words) != len(confidence_scores):
            self.logger.warning(f"Mismatch: {len(words)} words, {len(confidence_scores)} scores")
            # Pad or truncate to match
            if len(confidence_scores) < len(words):
                confidence_scores.extend([1.0] * (len(words) - len(confidence_scores)))
            else:
                confidence_scores = confidence_scores[:len(words)]
        
        filtered_words = []
        filtered_confidences = []
        
        for word, confidence in zip(words, confidence_scores):
            if confidence >= self.confidence_threshold:
                filtered_words.append(word)
                filtered_confidences.append(confidence)
        
        return ' '.join(filtered_words), filtered_confidences
    
    def get_caption_history(self, language: str, limit: int = None) -> List[CaptionEntry]:
        """
        Get caption history for a specific language
        
        Args:
            language: Language code
            limit: Maximum number of entries to return
        
        Returns:
            List of CaptionEntry objects
        """
        with self.lock:
            history = list(self.caption_history.get(language, []))
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_current_preview(self, language: str) -> Optional[CaptionEntry]:
        """Get the current preview caption for a language"""
        with self.lock:
            return self.current_previews.get(language)
    
    def get_all_captions_for_display(self, language: str) -> Tuple[List[CaptionEntry], Optional[CaptionEntry]]:
        """
        Get all finalized captions and current preview for display
        
        Args:
            language: Language code
        
        Returns:
            Tuple of (history_list, current_preview)
        """
        with self.lock:
            history = list(self.caption_history.get(language, []))
            preview = self.current_previews.get(language)
        
        return history, preview
    
    def clear_history(self, language: Optional[str] = None) -> None:
        """
        Clear caption history
        
        Args:
            language: Specific language to clear, or None for all
        """
        with self.lock:
            if language:
                if language in self.caption_history:
                    self.caption_history[language].clear()
                    self.current_previews[language] = None
                    self.logger.info(f"Cleared caption history for {language}")
                else:
                    self.logger.warning(f"Unknown language for clearing: {language}")
            else:
                # Clear all languages
                for lang in self.caption_history:
                    self.caption_history[lang].clear()
                    self.current_previews[lang] = None
                self.logger.info("Cleared all caption histories")
    
    def get_confidence_statistics(self, language: str) -> Dict[str, Any]:
        """
        Get confidence statistics for a language
        
        Args:
            language: Language code
        
        Returns:
            Dictionary with confidence statistics
        """
        with self.lock:
            history = list(self.caption_history.get(language, []))
        
        if not history:
            return {
                'total_captions': 0,
                'average_confidence': 0.0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0
            }
        
        all_confidences = []
        for entry in history:
            all_confidences.extend(entry.filtered_confidences)
        
        if not all_confidences:
            return {
                'total_captions': len(history),
                'average_confidence': 0.0,
                'high_confidence_count': 0,
                'medium_confidence_count': 0,
                'low_confidence_count': 0
            }
        
        # Calculate statistics
        total_captions = len(history)
        average_confidence = sum(all_confidences) / len(all_confidences)
        
        high_confidence_count = sum(1 for conf in all_confidences if conf >= 0.85)
        medium_confidence_count = sum(1 for conf in all_confidences if 0.65 <= conf < 0.85)
        low_confidence_count = sum(1 for conf in all_confidences if conf < 0.65)
        
        return {
            'total_captions': total_captions,
            'average_confidence': round(average_confidence, 3),
            'high_confidence_count': high_confidence_count,
            'medium_confidence_count': medium_confidence_count,
            'low_confidence_count': low_confidence_count,
            'total_words': len(all_confidences)
        }
    
    def get_text_color_for_confidence(self, confidence: float) -> str:
        """
        Get text color based on confidence level
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
        
        Returns:
            Color string for text display
        """
        if confidence >= 0.85:
            return 'green'
        elif confidence >= 0.65:
            return 'yellow'
        elif confidence >= 0.5:
            return 'red'
        else:
            return 'white'
    
    def export_captions(self, language: str, format_type: str = 'text') -> str:
        """
        Export captions in specified format
        
        Args:
            language: Language code
            format_type: Export format ('text', 'json', 'srt')
        
        Returns:
            Exported captions as string
        """
        with self.lock:
            history = list(self.caption_history.get(language, []))
        
        if format_type == 'text':
            return self._export_as_text(history)
        elif format_type == 'json':
            return self._export_as_json(history)
        elif format_type == 'srt':
            return self._export_as_srt(history)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_as_text(self, history: List[CaptionEntry]) -> str:
        """Export captions as plain text"""
        lines = []
        for entry in history:
            timestamp = time.strftime('%H:%M:%S', time.localtime(entry.timestamp))
            lines.append(f"[{timestamp}] {entry.filtered_text}")
        return '\n'.join(lines)
    
    def _export_as_json(self, history: List[CaptionEntry]) -> str:
        """Export captions as JSON"""
        import json
        
        data = []
        for entry in history:
            data.append({
                'text': entry.filtered_text,
                'confidence_scores': entry.filtered_confidences,
                'timestamp': entry.timestamp,
                'language': entry.language
            })
        
        return json.dumps(data, indent=2)
    
    def _export_as_srt(self, history: List[CaptionEntry]) -> str:
        """Export captions as SRT subtitle format"""
        lines = []
        
        for i, entry in enumerate(history, 1):
            start_time = self._seconds_to_srt_time(entry.timestamp - 2.0)  # Assume 2 second duration
            end_time = self._seconds_to_srt_time(entry.timestamp)
            
            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(entry.filtered_text)
            lines.append("")  # Empty line between entries
        
        return '\n'.join(lines)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get overall processing statistics"""
        with self.lock:
            total_captions = sum(len(history) for history in self.caption_history.values())
            active_languages = [lang for lang, history in self.caption_history.items() if history]
        
        return {
            'total_captions': total_captions,
            'active_languages': active_languages,
            'confidence_threshold': self.confidence_threshold,
            'max_history': self.max_history,
            'processing_enabled': True
        }
    
    def update_confidence_threshold(self, new_threshold: float) -> None:
        """Update the confidence threshold for filtering"""
        if 0.0 <= new_threshold <= 1.0:
            self.confidence_threshold = new_threshold
            self.logger.info(f"Confidence threshold updated to {new_threshold}")
        else:
            self.logger.error(f"Invalid confidence threshold: {new_threshold}")
    
    def shutdown(self) -> None:
        """Shutdown the caption processor"""
        self.logger.info("Shutting down caption processor")
        
        with self.lock:
            # Clear all data
            for lang in self.caption_history:
                self.caption_history[lang].clear()
                self.current_previews[lang] = None
        
        self.logger.info("Caption processor shutdown complete")