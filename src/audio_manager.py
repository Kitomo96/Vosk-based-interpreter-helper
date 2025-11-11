"""
Audio Manager for Vosk-based Interpreter Helper
Handles all audio device management, streaming, and callbacks
"""

import pyaudio
import queue
import threading
import logging
from typing import Callable, Optional, List, Tuple, Dict, Any
import json

class AudioDevice:
    """Represents an audio input device"""
    
    def __init__(self, index: int, name: str, max_input_channels: int, default_sample_rate: float):
        self.index = index
        self.name = name
        self.max_input_channels = max_input_channels
        self.default_sample_rate = default_sample_rate
    
    def __str__(self):
        return f"AudioDevice({self.index}, '{self.name}', {self.max_input_channels} channels)"
    
    def __repr__(self):
        return self.__str__()

class AudioManager:
    """
    Manages all audio operations including device enumeration, streaming, and callbacks
    """
    
    def __init__(self, config_manager, callback: Optional[Callable] = None):
        self.config_manager = config_manager
        self.audio_config = config_manager.get_audio_config()
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # Audio system
        self.audio = None
        self.stream = None
        self.audio_queue = queue.Queue()
        
        # Device management
        self.available_devices = []
        self.current_device_index = None
        self.default_device_index = None
        
        # State
        self.is_recording = False
        self.is_running = False
        
        # Initialize audio system
        self._initialize_audio_system()
    
    def _initialize_audio_system(self) -> None:
        """Initialize the audio system and enumerate devices"""
        try:
            self.audio = pyaudio.PyAudio()
            self.available_devices = self._get_available_devices()
            self.default_device_index = self._get_default_device_index()
            self.current_device_index = self.default_device_index
            
            self.logger.info(f"Audio system initialized with {len(self.available_devices)} devices")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio system: {e}")
            raise
    
    def _get_available_devices(self) -> List[AudioDevice]:
        """Get list of available audio input devices"""
        devices = []
        try:
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    device = AudioDevice(
                        index=i,
                        name=device_info['name'],
                        max_input_channels=device_info['maxInputChannels'],
                        default_sample_rate=device_info.get('defaultSampleRate', 16000.0)
                    )
                    devices.append(device)
        except Exception as e:
            self.logger.error(f"Failed to enumerate audio devices: {e}")
        
        return devices
    
    def _get_default_device_index(self) -> Optional[int]:
        """Get the default audio input device index"""
        try:
            default_device = self.audio.get_default_input_device_info()
            return default_device['index']
        except Exception as e:
            self.logger.error(f"Failed to get default audio device: {e}")
            return None
    
    def get_devices_info(self) -> List[Dict[str, Any]]:
        """Get formatted device information for UI"""
        return [
            {
                'index': device.index,
                'name': device.name,
                'channels': device.max_input_channels,
                'sample_rate': device.default_sample_rate,
                'is_default': device.index == self.default_device_index
            }
            for device in self.available_devices
        ]
    
    def set_device(self, device_index: int) -> bool:
        """Set the current audio input device"""
        if device_index == self.current_device_index:
            return True
        
        # Validate device index
        if not any(device.index == device_index for device in self.available_devices):
            self.logger.error(f"Invalid device index: {device_index}")
            return False
        
        # Restart stream with new device
        was_recording = self.is_recording
        self.stop_stream()
        
        self.current_device_index = device_index
        
        if was_recording:
            return self.start_stream()
        
        return True
    
    def start_stream(self) -> bool:
        """Start the audio stream"""
        if self.is_recording:
            self.logger.warning("Audio stream already running")
            return True
        
        try:
            audio_config = self.audio_config
            
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=audio_config['channels'],
                rate=audio_config['sample_rate'],
                input=True,
                frames_per_buffer=audio_config['chunk_size'],
                input_device_index=self.current_device_index,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            self.is_recording = True
            self.is_running = True
            
            device_name = self._get_device_name()
            self.logger.info(f"Audio stream started - Device: {device_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {e}")
            return False
    
    def stop_stream(self) -> None:
        """Stop the audio stream"""
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except Exception as e:
                self.logger.error(f"Error stopping audio stream: {e}")
        
        self.is_recording = False
        self.logger.info("Audio stream stopped")
    
    def _audio_callback(self, in_data: bytes, frame_count: int, time_info: dict, status: int) -> Tuple[None, int]:
        """Audio stream callback function"""
        if status:
            self.logger.warning(f"Audio callback status: {status}")
        
        if in_data:
            self.audio_queue.put(bytes(in_data))
        
        return (None, pyaudio.paContinue)
    
    def _get_device_name(self) -> str:
        """Get the name of the current device"""
        for device in self.available_devices:
            if device.index == self.current_device_index:
                return device.name
        return "Unknown Device"
    
    def get_audio_data(self, timeout: float = 0.1) -> Optional[bytes]:
        """Get audio data from the queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def is_audio_available(self) -> bool:
        """Check if audio data is available"""
        return not self.audio_queue.empty()
    
    def clear_queue(self) -> None:
        """Clear the audio data queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def get_current_device_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current device"""
        for device in self.available_devices:
            if device.index == self.current_device_index:
                return {
                    'index': device.index,
                    'name': device.name,
                    'channels': device.max_input_channels,
                    'sample_rate': device.default_sample_rate
                }
        return None
    
    def test_device(self, device_index: int, duration_seconds: float = 2.0) -> Dict[str, Any]:
        """Test a specific audio device"""
        try:
            # Temporarily switch to test device
            original_device = self.current_device_index
            self.current_device_index = device_index
            
            # Start stream for testing
            test_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.audio_config['channels'],
                rate=self.audio_config['sample_rate'],
                input=True,
                frames_per_buffer=self.audio_config['chunk_size'],
                input_device_index=device_index
            )
            
            test_stream.start_stream()
            
            # Record for specified duration
            import time
            start_time = time.time()
            audio_data = []
            
            while time.time() - start_time < duration_seconds:
                data = test_stream.read(self.audio_config['chunk_size'], exception_on_overflow=False)
                audio_data.append(data)
            
            test_stream.stop_stream()
            test_stream.close()
            
            # Restore original device
            self.current_device_index = original_device
            
            # Analyze the recorded data
            total_frames = len(audio_data) * self.audio_config['chunk_size']
            
            return {
                'success': True,
                'device_index': device_index,
                'duration_tested': duration_seconds,
                'frames_recorded': total_frames,
                'audio_level': self._calculate_audio_level(audio_data),
                'has_audio': total_frames > 0
            }
            
        except Exception as e:
            self.logger.error(f"Device test failed for device {device_index}: {e}")
            return {
                'success': False,
                'device_index': device_index,
                'error': str(e)
            }
    
    def _calculate_audio_level(self, audio_data: List[bytes]) -> float:
        """Calculate average audio level from recorded data"""
        import numpy as np
        
        # Convert audio data to numpy array
        audio_array = np.frombuffer(b''.join(audio_data), dtype=np.int16)
        
        # Calculate RMS (Root Mean Square) as audio level indicator
        rms = np.sqrt(np.mean(audio_array**2))
        return float(rms)
    
    def shutdown(self) -> None:
        """Shutdown the audio manager"""
        self.logger.info("Shutting down audio manager")
        
        self.stop_stream()
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        self.clear_queue()
        self.is_running = False
        
        self.logger.info("Audio manager shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'is_running') and self.is_running:
            self.shutdown()