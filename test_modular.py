"""
Test script for the modular LiveCaptioner implementation
"""

import sys
import os
sys.path.insert(0, 'src')

def test_modular_implementation():
    """Test the modular implementation without UI"""
    print("=" * 60)
    print("TESTING MODULAR IMPLEMENTATION")
    print("=" * 60)
    
    try:
        # Test imports
        print("\n1. Testing Imports...")
        from configuration_manager import ConfigurationManager
        from audio_manager import AudioManager
        from speech_recognition_engine import SpeechRecognitionEngine
        from caption_processor import CaptionProcessor
        print("OK All imports successful")
        
        # Test configuration
        print("\n2. Testing Configuration...")
        config = ConfigurationManager('../config/settings.ini')  # Fixed path for src directory
        audio_config = config.get_audio_config()
        print(f"OK Config loaded: Sample rate = {audio_config['sample_rate']}")
        
        # Test caption processor
        print("\n3. Testing Caption Processor...")
        processor = CaptionProcessor(config)
        stats = processor.get_processing_stats()
        print(f"OK Processor initialized: {stats['total_captions']} captions")
        
        # Test audio manager (no UI)
        print("\n4. Testing Audio Manager...")
        audio_manager = AudioManager(config)
        devices = audio_manager.get_devices_info()
        print(f"OK Audio system: {len(devices)} devices detected")
        
        # Test speech recognition
        print("\n5. Testing Speech Recognition...")
        def dummy_callback(result):
            pass
        
        speech_engine = SpeechRecognitionEngine(config, dummy_callback)
        model_tests = speech_engine.test_model_loading()
        
        print("OK Speech recognition initialized")
        print("Model test results:")
        for lang, status in model_tests.items():
            status_str = "LOADED" if status else "FAILED"
            print(f"  {lang}: {status_str}")
        
        # Test complete system
        print("\n6. Testing LiveCaptioner Integration...")
        from live_captioner_modular import LiveCaptioner
        
        # Create without UI - fixed path for src directory
        app = LiveCaptioner('../config/settings.ini')
        test_results = app.test_all_components()
        
        print("OK LiveCaptioner created and tested")
        overall_success = test_results.get('overall_success', False)
        
        print(f"\nFINAL RESULT: {'SUCCESS' if overall_success else 'FAILED'}")
        
        if overall_success:
            print("\nMODULAR IMPLEMENTATION IS WORKING PERFECTLY!")
            print("OK All components loaded successfully")
            print("OK All Vosk models loaded")
            print("OK Audio system working")
            print("OK Configuration system working")
            print("OK Speech recognition working")
            print("\nThe refactored, modular architecture is ready for production!")
        else:
            print("\nSome components failed to load")
            
        return overall_success
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_modular_implementation()
    sys.exit(0 if success else 1)