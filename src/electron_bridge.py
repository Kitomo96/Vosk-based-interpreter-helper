import sys
import json
import logging
import signal
import time
import threading
from configuration_manager import ConfigurationManager
from audio_manager import AudioManager
from speech_recognition_engine import SpeechRecognitionEngine

# Configure logging to stderr so stdout is clean for JSON
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("ElectronBridge")

# Global reference for the speech engine to be accessed by the listener
speech_engine = None

def result_callback(result):
    """
    Callback for speech recognition results.
    Formats the result as JSON and prints to stdout for Electron to capture.
    """
    try:
        message = {
            "type": "transcription",
            "text": result.text,
            "is_final": result.is_final,
            "language": result.language,
            "confidence": result.confidence_scores,
            "timestamp": result.timestamp
        }
        # Print JSON line to stdout (flush immediately)
        print(json.dumps(message), flush=True)
    except Exception as e:
        logger.error(f"Error in callback: {e}")

def stdin_listener():
    """
    Listens for commands from Electron via stdin
    """
    global speech_engine
    logger.info("Stdin listener started")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
            
            # DEBUG: Print received line to stderr
            sys.stderr.write(f"DEBUG: Received stdin: {line}\n")
            sys.stderr.flush()
            
            try:
                data = json.loads(line)
                command = data.get('command')
                
                if command == 'set_languages':
                    languages = data.get('languages', [])
                    sys.stderr.write(f"DEBUG: Processing set_languages: {languages}\n")
                    sys.stderr.flush()
                    
                    if speech_engine:
                        speech_engine.set_active_languages(languages)
                    else:
                        logger.warning("Speech engine not initialized yet")
                        
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from stdin: {line}")
            except Exception as e:
                logger.error(f"Error processing stdin command: {e}")
                
        except Exception as e:
            logger.error(f"Error in stdin listener: {e}")
            time.sleep(1)

def main():
    global speech_engine
    logger.info("Starting Electron Bridge...")
    
    try:
        # Initialize config
        config_manager = ConfigurationManager("../config/settings.ini")
        
        # Initialize audio
        audio_manager = AudioManager(config_manager)
        if not audio_manager.start_stream():
            logger.error("Failed to start audio stream")
            sys.exit(1)
            
        # Initialize speech engine
        speech_engine = SpeechRecognitionEngine(
            config_manager,
            result_callback=result_callback
        )
        
        if not speech_engine.start_recognition(audio_manager):
            logger.error("Failed to start recognition")
            sys.exit(1)
            
        # Start stdin listener thread
        listener_thread = threading.Thread(target=stdin_listener, daemon=True)
        listener_thread.start()
            
        logger.info("Bridge is running. Waiting for audio...")
        # Send ready signal to frontend
        print(json.dumps({"type": "status", "message": "ready"}), flush=True)
        
        # Keep alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping bridge...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if speech_engine:
            speech_engine.stop_recognition()
        if 'audio_manager' in locals():
            audio_manager.stop_stream()

if __name__ == "__main__":
    main()
