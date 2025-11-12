#!/usr/bin/env python3
"""
Debug script to trace text repetition issue
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, 'src')

from caption_processor import CaptionProcessor, CaptionEntry
from configuration_manager import ConfigurationManager

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_repetition_issue():
    """Test to reproduce and debug the repetition issue"""
    
    print("Testing Caption Processor for repetition issues...")
    
    # Create configuration and processor
    config = ConfigurationManager('../config/settings.ini')
    processor = CaptionProcessor(config)
    
    # Test sequence that should cause issues
    test_cases = [
        # Simulate partial results building up
        ("hello are you listening", False, 'en', [0.8, 0.9, 0.7, 0.8, 0.9]),
        ("hello are you listening to", False, 'en', [0.8, 0.9, 0.7, 0.8, 0.9, 0.8]),
        ("hello are you listening to me", False, 'en', [0.8, 0.9, 0.7, 0.8, 0.9, 0.8, 0.9]),
        
        # Final result
        ("hello are you listening to me speaking now", True, 'en', [0.8, 0.9, 0.7, 0.8, 0.9, 0.8, 0.9, 0.8, 0.7]),
        
        # Another sequence
        ("can we see both", False, 'en', [0.8, 0.9, 0.8, 0.9]),
        ("can we see both the text", False, 'en', [0.8, 0.9, 0.8, 0.9, 0.8, 0.9]),
        ("can we see both the text or", False, 'en', [0.8, 0.9, 0.8, 0.9, 0.8, 0.9, 0.8]),
        
        # Final result
        ("can we see both the text or partial results", True, 'en', [0.8, 0.9, 0.8, 0.9, 0.8, 0.9, 0.8, 0.7, 0.8]),
    ]
    
    print("Processing test sequence...")
    
    # Process each test case
    for i, (text, is_final, language, confidences) in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {'FINAL' if is_final else 'PARTIAL'} ---")
        print(f"Input: '{text}' (lang: {language})")
        
        # Process the result
        result = processor.process_recognition_result(
            text=text,
            is_final=is_final,
            language=language,
            confidence_scores=confidences
        )
        
        print(f"Returned result: {result}")
        
        # Check what's in history and preview
        history, preview = processor.get_all_captions_for_display(language)
        print(f"History count: {len(history)}")
        print(f"Preview: {preview.filtered_text if preview else 'None'}")
        
        for j, entry in enumerate(history):
            print(f"  History[{j}]: '{entry.filtered_text}' (final: {entry.is_final})")
    
    # Final check
    print(f"\n=== FINAL STATE ===")
    for language in ['en', 'es']:
        history, preview = processor.get_all_captions_for_display(language)
        print(f"{language.upper()}:")
        print(f"  History entries: {len(history)}")
        for j, entry in enumerate(history):
            print(f"    [{j}]: '{entry.filtered_text}' (ts: {entry.timestamp})")
        print(f"  Preview: {preview.filtered_text if preview else 'None'}")

if __name__ == "__main__":
    test_repetition_issue()