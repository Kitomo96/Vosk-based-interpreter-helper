"""
UI Manager for Vosk-based Interpreter Helper
Handles all Tkinter GUI components and user interface interactions
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
import threading
import logging
from typing import Optional, List, Dict, Any, Callable
import time

class CaptionDisplay:
    """Manages the caption display for a single language"""
    
    def __init__(self, parent_frame, language: str, language_name: str, 
                 base_font_size: int, min_font_size: int, max_font_size: int):
        self.language = language
        self.language_name = language_name
        self.base_font_size = base_font_size
        self.min_font_size = min_font_size
        self.max_font_size = max_font_size
        
        # Create frame
        self.frame = tk.Frame(
            parent_frame,
            bg='black',
            highlightthickness=1,
            highlightcolor='white'
        )
        
        # Create text widget (basic parameters to avoid crashes)
        self.text_widget = scrolledtext.ScrolledText(
            self.frame,
            font=('Segoe UI', base_font_size),
            fg='white',
            bg='black',
            wrap=tk.WORD,
            height=15,
            state='disabled'
        )
        
        self.text_widget.pack(expand=True, fill='both')
        
        # Initialize display
        self._initialize_display()
    
    def _initialize_display(self) -> None:
        """Initialize the text display with default styling"""
        # Initialize only the necessary tags (not alignment)
        self.text_widget.tag_configure('waiting',
                                     font=('Segoe UI', self.base_font_size + 2),
                                     foreground='lightgreen')
        self.text_widget.tag_configure('preview', foreground='gray')
        self.text_widget.tag_configure('center', justify='center')
        
        self.text_widget.config(state='normal')
        self.text_widget.insert('1.0', f'Waiting for {self.language_name} speech...')
        self.text_widget.tag_add('waiting', '1.0', 'end')
        self.text_widget.tag_add('center', '1.0', 'end')
        self.text_widget.config(state='disabled')
    
    def update_font_size(self, new_size: int) -> None:
        """Update font size for all text"""
        new_size = max(self.min_font_size, min(self.max_font_size, new_size))
        font = ('Segoe UI', new_size)
        
        self.text_widget.config(font=font)
        
        # Update waiting font size
        self.text_widget.tag_configure('waiting',
                                     font=('Segoe UI', new_size + 2))
    
    def clear_and_show_waiting(self) -> None:
        """Clear display and show waiting message"""
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', f'Waiting for {self.language_name} speech...')
        self.text_widget.tag_add('waiting', '1.0', 'end')
        self.text_widget.tag_add('center', '1.0', 'end')
        self.text_widget.config(state='disabled')
    
    def update_captions(self, history: List, preview: Optional[Dict] = None) -> None:
        """Update the caption display with new content (optimized to reduce flickering)"""
        
        # Check if content actually changed before updating
        current_content = self.text_widget.get('1.0', tk.END)
        
        # Build new content string for comparison
        new_content_lines = []
        
        # Add history captions
        for entry in history:
            text = entry.get('text', '')
            new_content_lines.append(text)
        
        # Add preview if available
        if preview:
            preview_text = preview.get('text', '')
            if preview_text:
                new_content_lines.append(preview_text)
        
        new_content = '\n'.join(new_content_lines)
        
        # Only update if content actually changed (prevents unnecessary flickering)
        if current_content.strip() != new_content.strip():
            self.text_widget.config(state='normal')
            self.text_widget.delete('1.0', tk.END)
            
            # Add history captions
            for entry in history:
                self._insert_colored_text(entry.get('text', ''), entry.get('confidence_scores', []))
                self.text_widget.insert(tk.END, '\n')
            
            # Add preview if available
            if preview:
                if preview.get('text') == "...":
                    self.text_widget.insert(tk.END, "...", 'preview')
                else:
                    self._insert_colored_text(preview.get('text', ''),
                                            preview.get('confidence_scores', []), True)
            
            # Only scroll to end if necessary (reduces scroll flicker)
            if self._should_scroll_to_end(current_content, new_content):
                self.text_widget.see(tk.END)
            
            self.text_widget.config(state='disabled')
    
    def _should_scroll_to_end(self, old_content: str, new_content: str) -> bool:
        """Determine if we should scroll to end (reduces unnecessary scroll flicker)"""
        old_lines = len(old_content.strip().split('\n')) if old_content.strip() else 0
        new_lines = len(new_content.strip().split('\n')) if new_content.strip() else 0
        
        # Scroll if: new content has more lines OR we were at the end before
        if new_lines > old_lines:
            return True
        
        # Check if we were already near the end
        if '...' in old_content or 'Waiting for' in old_content:
            return True
            
        return False
    
    def _insert_colored_text(self, text: str, confidence_scores: List[float], is_preview: bool = False) -> None:
        """Insert text with color coding based on confidence"""
        if not text:
            return
            
        words = text.split()
        
        for i, word in enumerate(words):
            # Determine color based on confidence
            if confidence_scores and i < len(confidence_scores):
                confidence = confidence_scores[i]
                color = self._get_color_for_confidence(confidence)
            else:
                color = 'white'
            
            tag_name = f"{self.language}_{color}"
            if tag_name not in [tag for tag in self.text_widget.tag_names()]:
                self.text_widget.tag_configure(tag_name, foreground=color)
            
            self.text_widget.insert(tk.END, word, tag_name)
            
            # Add space after word (except last word)
            if i < len(words) - 1:
                self.text_widget.insert(tk.END, ' ', tag_name)
        
        # Mark preview text
        if is_preview:
            preview_start = self.text_widget.index(f"end-{len(text)+1}c")
            self.text_widget.insert(tk.END, "")
            self.text_widget.tag_add('preview', preview_start, tk.END)
    
    def _get_color_for_confidence(self, confidence: float) -> str:
        """Get text color based on confidence level"""
        if confidence >= 0.85:
            return 'green'
        elif confidence >= 0.65:
            return 'yellow'
        elif confidence >= 0.5:
            return 'red'
        else:
            return 'white'

class UIManager:
    """
    Manages the Tkinter user interface for the interpreter helper
    """
    
    def __init__(self, config_manager, caption_processor):
        self.config_manager = config_manager
        self.caption_processor = caption_processor
        self.logger = logging.getLogger(__name__)
        
        # UI configuration
        self.ui_config = config_manager.get_ui_config()
        
        # Tkinter components
        self.root = None
        self.caption_displays = {}
        self.control_frame = None
        self.status_label = None
        self.language_indicator = None
        self.device_var = None
        self.device_menu = None
        
        # State
        self.is_running = False
        self.initial_window_size = None
        self.current_font_size = self.ui_config['font_size']
        
        # Event handlers
        self.device_change_callback = None
        self.clear_history_callback = None
        self.window_close_callback = None
        
        self.logger.info("UI Manager initialized")
    
    def initialize_ui(self) -> bool:
        """Initialize the Tkinter user interface"""
        try:
            self._create_main_window()
            self._create_caption_panels()
            self._create_control_panel()
            self._create_status_bar()
            self._setup_event_handlers()
            self._setup_responsive_layout()
            
            self.logger.info("UI components created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {e}")
            return False
    
    def _create_main_window(self) -> None:
        """Create the main application window"""
        self.root = tk.Tk()
        self.root.title("Live Captioner (Privacy Mode)")
        self.root.attributes('-topmost', True)
        
        # Set initial size
        width = self.ui_config['default_window_width']
        height = self.ui_config['default_window_height']
        self.root.geometry(f"{width}x{height}")
        self.root.configure(bg='black')
        
        # Store initial size for responsive scaling
        self.root.update_idletasks()
        self.initial_window_size = (self.root.winfo_width(), self.root.winfo_height())
        
        self.logger.info(f"Main window created: {width}x{height}")
    
    def _create_caption_panels(self) -> None:
        """Create side-by-side caption display panels"""
        # Main container
        history_container = tk.Frame(self.root, bg='black')
        history_container.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Configure equal column weights
        history_container.grid_columnconfigure(0, weight=1)
        history_container.grid_columnconfigure(1, weight=1)
        
        # Create caption displays
        languages = [
            ('en', 'English'),
            ('es', 'Spanish')
        ]
        
        for i, (lang_code, lang_name) in enumerate(languages):
            display = CaptionDisplay(
                history_container,
                lang_code,
                lang_name,
                self.ui_config['font_size'],
                self.ui_config['min_font_size'],
                self.ui_config['max_font_size']
            )
            
            display.frame.grid(row=0, column=i, padx=5, pady=5, sticky='nsew')
            self.caption_displays[lang_code] = display
        
        self.logger.info(f"Created {len(self.caption_displays)} caption panels")
    
    def _create_control_panel(self) -> None:
        """Create the control panel with buttons and settings"""
        self.control_frame = tk.Frame(self.root, bg='black')
        self.control_frame.pack(fill='x', pady=10, padx=20)
        
        # Privacy notice
        privacy_label = tk.Label(
            self.control_frame,
            text="🔒 Privacy Mode: No transcriptions are saved to disk",
            font=('Segoe UI', 10),
            fg='lightgreen',
            bg='black'
        )
        privacy_label.pack(fill='x', pady=(0, 10))
        
        # Audio device selector
        device_frame = tk.Frame(self.control_frame, bg='black')
        device_frame.pack(side='left', padx=5)
        
        tk.Label(device_frame, text="Audio Input:", font=('Segoe UI', 10), 
                fg='white', bg='black').pack(side='left')
        
        self.device_var = tk.StringVar()
        self.device_menu = ttk.Combobox(
            device_frame,
            textvariable=self.device_var,
            state="readonly",
            width=30
        )
        self.device_menu.pack(side='left', padx=5)
        
        # Control buttons
        buttons_frame = tk.Frame(self.control_frame, bg='black')
        buttons_frame.pack(side='left', padx=20)
        
        # Clear history button
        clear_button = tk.Button(
            buttons_frame,
            text="Clear All History",
            command=self._on_clear_history,
            bg='darkred',
            fg='white'
        )
        clear_button.pack(side='left', padx=5)
        
        # Language indicator
        self.language_indicator = tk.Label(
            self.control_frame,
            text="Detected Language: Unknown",
            font=('Segoe UI', 10),
            fg='white',
            bg='black'
        )
        self.language_indicator.pack(side='left', padx=20)
        
        self.logger.info("Control panel created")
    
    def _create_status_bar(self) -> None:
        """Create the status bar"""
        self.status_label = tk.Label(
            self.root,
            text="🎤 Initializing...",
            font=('Segoe UI', 10),
            fg='yellow',
            bg='black'
        )
        self.status_label.pack(side='bottom')
        
        self.logger.info("Status bar created")
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for window and controls"""
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Window resize event
        self.root.bind('<Configure>', self._on_window_resize)
        
        # Device selection event
        self.device_menu.bind('<<ComboboxSelected>>', self._on_device_change)
        
        self.logger.info("Event handlers configured")
    
    def _setup_responsive_layout(self) -> None:
        """Setup responsive layout configuration"""
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.logger.info("Responsive layout configured")
    
    def _on_window_resize(self, event) -> None:
        """Handle window resize events for font scaling"""
        if event.widget != self.root or not self.initial_window_size:
            return
        
        # Calculate scaling factor
        width_scale = event.width / self.initial_window_size[0]
        height_scale = event.height / self.initial_window_size[1]
        scale_factor = min(width_scale, height_scale)
        
        # Calculate new font size
        new_font_size = max(
            self.ui_config['min_font_size'],
            min(self.ui_config['max_font_size'], 
                int(self.ui_config['font_size'] * scale_factor))
        )
        
        if new_font_size != self.current_font_size:
            self.current_font_size = new_font_size
            
            # Update all caption displays
            for display in self.caption_displays.values():
                display.update_font_size(new_font_size)
            
            self.root.update_idletasks()
    
    def _on_device_change(self, event=None) -> None:
        """Handle audio device selection change"""
        if self.device_change_callback:
            device_name = self.device_var.get()
            try:
                self.device_change_callback(device_name)
            except Exception as e:
                self.logger.error(f"Error in device change callback: {e}")
    
    def _on_clear_history(self) -> None:
        """Handle clear history button click"""
        if self.clear_history_callback:
            try:
                self.clear_history_callback()
            except Exception as e:
                self.logger.error(f"Error in clear history callback: {e}")
    
    def _on_window_close(self) -> None:
        """Handle window close event"""
        if self.window_close_callback:
            try:
                self.window_close_callback()
            except Exception as e:
                self.logger.error(f"Error in window close callback: {e}")
        else:
            self.shutdown()
    
    def update_audio_devices(self, devices: List[Dict[str, Any]]) -> None:
        """Update the audio device dropdown"""
        if not self.device_menu:
            return
        
        device_names = [device['name'] for device in devices]
        self.device_menu['values'] = device_names
        
        # Set default device if available
        default_device = next((device for device in devices if device.get('is_default')), None)
        if default_device:
            self.device_var.set(default_device['name'])
        elif device_names:
            self.device_var.set(device_names[0])
        
        self.logger.info(f"Updated device list with {len(devices)} devices")
    
    def update_captions(self, language: str) -> None:
        """Update caption display for a specific language"""
        if language not in self.caption_displays:
            return
        
        display = self.caption_displays[language]
        
        # Get caption data from processor
        history, preview = self.caption_processor.get_all_captions_for_display(language)
        
        # Convert to display format
        history_data = []
        for entry in history:
            history_data.append({
                'text': entry.filtered_text,
                'confidence_scores': entry.filtered_confidences
            })
        
        preview_data = None
        if preview:
            preview_data = {
                'text': preview.filtered_text,
                'confidence_scores': preview.filtered_confidences
            }
        
        # Update display
        display.update_captions(history_data, preview_data)
    
    def update_all_captions(self) -> None:
        """Update captions for all languages"""
        for language in self.caption_displays.keys():
            self.update_captions(language)
    
    def update_status(self, message: str, color: str = 'green') -> None:
        """Update status label"""
        if self.status_label:
            self.status_label.config(text=message, fg=color)
    
    def update_language_detection(self, language: str, confidence: float = None) -> None:
        """Update language detection indicator with confidence"""
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'unknown': 'Detecting...'
        }
        
        language_name = language_names.get(language, language.upper())
        
        # Add confidence indicator
        if confidence is not None:
            confidence_indicator = self._get_confidence_indicator(confidence)
            display_text = f"Language: {language_name} ({confidence_indicator})"
        else:
            display_text = f"Language: {language_name}"
        
        if self.language_indicator:
            self.language_indicator.config(text=display_text)
    
    def _get_confidence_indicator(self, confidence: float) -> str:
        """Get confidence indicator based on confidence score"""
        if confidence >= 0.8:
            return f"High ({confidence:.0%})"
        elif confidence >= 0.6:
            return f"Medium ({confidence:.0%})"
        elif confidence >= 0.3:
            return f"Low ({confidence:.0%})"
        else:
            return f"Uncertain ({confidence:.0%})"
    
    def show_language_detection_panel(self, detection_stats: Dict[str, Any]) -> None:
        """Show detailed language detection statistics"""
        # Create or update detection statistics display
        if not hasattr(self, 'detection_stats_frame'):
            self._create_detection_stats_frame()
        
        detected_lang = detection_stats.get('detected_language', 'unknown')
        confidence = detection_stats.get('confidence', 0.0)
        language_breakdown = detection_stats.get('language_breakdown', {})
        
        # Update the display
        language_names = {'en': 'English', 'es': 'Spanish', 'fr': 'French', 'unknown': 'Unknown'}
        
        stats_text = f"Detected: {language_names.get(detected_lang, detected_lang)}\n"
        stats_text += f"Confidence: {confidence:.1%}\n"
        stats_text += "Language Distribution:\n"
        
        for lang, percentage in language_breakdown.items():
            lang_name = language_names.get(lang, lang.upper())
            stats_text += f"  {lang_name}: {percentage:.1f}%\n"
        
        self.detection_stats_text.config(state=tk.NORMAL)
        self.detection_stats_text.delete('1.0', tk.END)
        self.detection_stats_text.insert('1.0', stats_text)
        self.detection_stats_text.config(state=tk.DISABLED)
    
    def _create_detection_stats_frame(self) -> None:
        """Create frame for displaying language detection statistics"""
        self.detection_stats_frame = tk.Frame(self.root, relief=tk.RAISED, bd=1)
        self.detection_stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Title
        title_label = tk.Label(self.detection_stats_frame, text="Language Detection", font=('Arial', 10, 'bold'))
        title_label.pack(pady=(10, 5))
        
        # Statistics text widget
        self.detection_stats_text = tk.Text(self.detection_stats_frame, height=8, width=25, wrap=tk.WORD)
        self.detection_stats_text.pack(padx=10, pady=(0, 10))
        self.detection_stats_text.config(state=tk.DISABLED)
        
        # Manual language selection buttons
        manual_frame = tk.Frame(self.detection_stats_frame)
        manual_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(manual_frame, text="Manual Override:", font=('Arial', 8, 'bold')).pack(anchor=tk.W)
        
        button_frame = tk.Frame(manual_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.manual_lang_vars = {}
        for lang in ['en', 'es', 'fr']:
            var = tk.BooleanVar()
            self.manual_lang_vars[lang] = var
            btn = tk.Checkbutton(button_frame, text=lang.upper(), variable=var,
                               command=lambda l=lang: self._on_manual_language_select(l))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Reset button
        reset_btn = tk.Button(manual_frame, text="Reset Detection", command=self._reset_language_detection)
        reset_btn.pack(pady=5)
    
    def _on_manual_language_select(self, language: str) -> None:
        """Handle manual language selection"""
        # Clear other selections
        for lang, var in self.manual_lang_vars.items():
            if lang != language:
                var.set(False)
        
        # Notify the application about manual language selection
        if hasattr(self, 'on_language_override_callback'):
            self.on_language_override_callback(language)
    
    def _reset_language_detection(self) -> None:
        """Reset language detection to automatic mode"""
        for var in self.manual_lang_vars.values():
            var.set(False)
        
        # Notify the application about reset
        if hasattr(self, 'on_language_reset_callback'):
            self.on_language_reset_callback()
    
    def hide_language_detection_panel(self) -> None:
        """Hide the language detection statistics panel"""
        if hasattr(self, 'detection_stats_frame'):
            self.detection_stats_frame.pack_forget()
    
    def set_language_callbacks(self, override_callback=None, reset_callback=None) -> None:
        """Set callbacks for language override and reset actions"""
        self.on_language_override_callback = override_callback
        self.on_language_reset_callback = reset_callback
    
    def show_visual_feedback(self) -> None:
        """Show visual feedback (brief status change)"""
        if self.status_label:
            original_color = self.status_label.cget('fg')
            self.status_label.config(fg='yellow')
            
            # Restore original color after brief delay
            def restore():
                if self.status_label:
                    self.status_label.config(fg=original_color)
            
            self.root.after(100, restore)
    
    def get_window(self) -> tk.Tk:
        """Get the main Tkinter window object"""
        return self.root
    
    def set_device_change_callback(self, callback: Callable) -> None:
        """Set callback for device change events"""
        self.device_change_callback = callback
    
    def set_clear_history_callback(self, callback: Callable) -> None:
        """Set callback for clear history events"""
        self.clear_history_callback = callback
    
    def set_window_close_callback(self, callback: Callable) -> None:
        """Set callback for window close events"""
        self.window_close_callback = callback
    
    def start_mainloop(self) -> None:
        """Start the Tkinter main loop"""
        if self.root:
            self.is_running = True
            self.root.mainloop()
            self.is_running = False
    
    def stop_mainloop(self) -> None:
        """Stop the Tkinter main loop"""
        if self.root and self.is_running:
            self.root.quit()
            self.root.destroy()
            self.root = None
            self.is_running = False
    
    def is_ui_running(self) -> bool:
        """Check if UI is currently running"""
        return self.is_running and self.root is not None
    
    def shutdown(self) -> None:
        """Shutdown the UI manager"""
        self.logger.info("Shutting down UI manager")
        
        if self.root:
            self.stop_mainloop()
        
        # Clear references
        self.caption_displays.clear()
        self.control_frame = None
        self.status_label = None
        self.language_indicator = None
        self.device_var = None
        self.device_menu = None
        
        self.logger.info("UI manager shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'is_running') and self.is_running:
            self.shutdown()