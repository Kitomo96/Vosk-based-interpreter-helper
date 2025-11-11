import vosk
import pyaudio
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import queue

class LiveCaptioner:
    def __init__(self):
        # Initialize audio settings
        self.CHUNK = 1024  # Number of audio frames per buffer
        self.RATE = 16000  # Sampling rate in Hz
        self.audio_queue = queue.Queue()  # Queue to store audio data
        
        # Initialize caption history and settings
        self.caption_history_en = []  # Store English captions
        self.caption_history_es = []  # Store Spanish captions
        self.max_history = 100  # Maximum number of captions to store
        self.current_preview_en = None  # Current preview for English
        self.current_preview_es = None  # Current preview for Spanish
        self.confidence_threshold = 0.5  # Minimum confidence for word inclusion
        
        # Set up audio devices
        self.audio = pyaudio.PyAudio()
        self.available_devices = self.get_audio_devices()
        self.current_device_index = self.get_default_device_index()
        
        # Initialize language models
        self.models = {
            "en": vosk.Model("vosk-model-small-en-us"),  # English model
            "es": vosk.Model("vosk-model-small-es")  # Spanish model
        }
        
        # Initialize speech recognizers
        self.recognizers = {
            "en": vosk.KaldiRecognizer(self.models["en"], self.RATE),
            "es": vosk.KaldiRecognizer(self.models["es"], self.RATE)
        }
        
        # Enable word-level timestamps
        for recognizer in self.recognizers.values():
            recognizer.SetWords(True)
            
        # Add new attributes
        self.sentence_started = {"en": False, "es": False}
        self.word_count = {"en": 0, "es": 0}
        self.initial_finalization_threshold = 4
        self.long_sentence_threshold = 10
        
        self.base_font_size = 12  # Set this to your current preferred font size
        self.current_font_size = self.base_font_size
        self.min_font_size = self.base_font_size - 2
        self.max_font_size = self.base_font_size + 2
        
        # Add language detection attribute
        self.current_language = "Unknown"
        
        self.setup_ui()  # Set up the user interface

    def get_audio_devices(self):
        # Get a list of available audio input devices
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # Only input devices
                devices.append((i, device_info['name']))
        return devices

    def get_default_device_index(self):
        # Get the index of the default audio input device
        default_device = self.audio.get_default_input_device_info()
        return default_device['index']

    def setup_ui(self):
        # Set up the main window and UI components
        self.root = tk.Tk()
        self.root.title("Live Captioner (Privacy Mode)")
        self.root.attributes('-topmost', True)
        self.root.geometry("1200x800")
        self.root.configure(bg='black')
        
        # Main container
        self.main_frame = tk.Frame(self.root, bg='black')
        self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Privacy notice
        self.privacy_label = tk.Label(
            self.main_frame,
            text="🔒 Privacy Mode: No transcriptions are saved to disk",
            font=('Segoe UI', 10),
            fg='lightgreen',
            bg='black'
        )
        self.privacy_label.pack(fill='x', pady=(0, 10))
        
        # Create frame for side-by-side boxes with equal width
        self.history_container = tk.Frame(self.main_frame, bg='black')
        self.history_container.pack(expand=True, fill='both')
        
        # Configure equal column weights
        self.history_container.grid_columnconfigure(0, weight=1)
        self.history_container.grid_columnconfigure(1, weight=1)
        
        # English box (left side)
        self.en_frame = tk.Frame(
            self.history_container,
            bg='black',
            highlightthickness=1,
            highlightcolor='white'
        )
        self.en_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        
        self.caption_history_widget_en = scrolledtext.ScrolledText(
            self.en_frame,
            font=('Segoe UI', 12),
            fg='white',
            bg='black',
            wrap=tk.WORD,
            height=15
        )
        self.caption_history_widget_en.pack(expand=True, fill='both')
        self.caption_history_widget_en.insert('1.0', 'Waiting for speech...')
        
        # Configure tags for text styling
        self.caption_history_widget_en.tag_configure('center', justify='center')
        self.caption_history_widget_en.tag_configure('waiting', 
                                                   font=('Segoe UI', 16),
                                                   foreground='lightgreen')
        self.caption_history_widget_en.tag_configure('preview',
                                                   foreground='gray')
        self.caption_history_widget_en.tag_configure('red', foreground='red')
        self.caption_history_widget_en.tag_configure('yellow', foreground='yellow')
        self.caption_history_widget_en.tag_configure('green', foreground='green')
        self.caption_history_widget_en.tag_configure('white', foreground='white')
        self.caption_history_widget_en.tag_add('center', '1.0', 'end')
        self.caption_history_widget_en.tag_add('waiting', '1.0', 'end')
        
        # Spanish box (right side)
        self.es_frame = tk.Frame(
            self.history_container,
            bg='black',
            highlightthickness=1,
            highlightcolor='white'
        )
        self.es_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        
        self.caption_history_widget_es = scrolledtext.ScrolledText(
            self.es_frame,
            font=('Segoe UI', 12),
            fg='white',
            bg='black',
            wrap=tk.WORD,
            height=15
        )
        self.caption_history_widget_es.pack(expand=True, fill='both')
        self.caption_history_widget_es.insert('1.0', 'Waiting for speech...')
        
        # Configure tags for text styling (same as English)
        self.caption_history_widget_es.tag_configure('center', justify='center')
        self.caption_history_widget_es.tag_configure('waiting', 
                                                   font=('Segoe UI', 16),
                                                   foreground='lightgreen')
        self.caption_history_widget_es.tag_configure('preview',
                                                   foreground='gray')
        self.caption_history_widget_es.tag_configure('red', foreground='red')
        self.caption_history_widget_es.tag_configure('yellow', foreground='yellow')
        self.caption_history_widget_es.tag_configure('green', foreground='green')
        self.caption_history_widget_es.tag_configure('white', foreground='white')
        self.caption_history_widget_es.tag_add('center', '1.0', 'end')
        self.caption_history_widget_es.tag_add('waiting', '1.0', 'end')
        
        # Control frame
        self.control_frame = tk.Frame(self.main_frame, bg='black')
        self.control_frame.pack(fill='x', pady=10)
        
        # Audio device selector
        self.device_var = tk.StringVar()
        self.device_menu = ttk.Combobox(
            self.control_frame,
            textvariable=self.device_var,
            values=[device[1] for device in self.available_devices],
            state="readonly",
            width=30
        )
        self.device_menu.pack(side='left', padx=5)
        self.device_menu.bind('<<ComboboxSelected>>', self.change_audio_device)
        
        # Set default device
        default_device_name = self.audio.get_device_info_by_index(
            self.current_device_index)['name']
        self.device_var.set(default_device_name)
        
        # Clear history button
        self.clear_button = tk.Button(
            self.control_frame,
            text="Clear All History",
            command=self.clear_history,
            bg='darkred',
            fg='white'
        )
        self.clear_button.pack(side='left', padx=5)
        
        # Status indicator
        self.status_label = tk.Label(
            self.main_frame,
            text="🎤 Active",
            font=('Segoe UI', 10),
            fg='green',
            bg='black'
        )
        self.status_label.pack(side='bottom')
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Configure row and column weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.main_frame.grid_rowconfigure(1, weight=1)  # Assuming history_container is in row 1
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.history_container.grid_rowconfigure(0, weight=1)
        self.history_container.grid_columnconfigure(0, weight=1)
        self.history_container.grid_columnconfigure(1, weight=1)

        # Use grid instead of pack for resizable widgets
        self.en_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.es_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        # Bind the resize event
        self.root.bind('<Configure>', self.on_window_resize)

        # Add language indicator
        self.language_indicator = tk.Label(
            self.control_frame,
            text="Detected Language: Unknown",
            font=('Segoe UI', 10),
            fg='white',
            bg='black'
        )
        self.language_indicator.pack(side='left', padx=5)

    def on_window_resize(self, event):
        # Store the initial size of the window when setting up the UI
        if not hasattr(self, 'initial_window_size'):
            self.initial_window_size = (event.width, event.height)
            return

        # Calculate scaling factor based on window size change
        width_scale = event.width / self.initial_window_size[0]
        height_scale = event.height / self.initial_window_size[1]
        scale_factor = min(width_scale, height_scale)  # Use the smaller scale to maintain aspect ratio

        # Calculate new font size
        new_font_size = max(self.min_font_size, min(self.max_font_size, int(self.base_font_size * scale_factor)))

        if new_font_size != self.current_font_size:
            self.current_font_size = new_font_size
            font = ('Segoe UI', self.current_font_size)
            
            # Update font size for both text widgets
            self.caption_history_widget_en.configure(font=font)
            self.caption_history_widget_es.configure(font=font)
            
            # Update tag configurations
            for widget in [self.caption_history_widget_en, self.caption_history_widget_es]:
                widget.tag_configure('waiting', font=(font[0], font[1] + 2))
                for tag in ['preview', 'red', 'yellow', 'green', 'white']:
                    widget.tag_configure(tag, font=font)

        # Resize the history container
        new_width = max(400, int(self.initial_window_size[0] * width_scale) - 40)
        new_height = max(300, int(self.initial_window_size[1] * height_scale) - 200)
        self.history_container.config(width=new_width, height=new_height)

        # Force update of the UI
        self.root.update_idletasks()

    def update_caption(self, text, is_final=False, lang=None, word_confidences=None):
        if not text:
            return
        
        # Get the appropriate widget and history list based on language
        widget = (self.caption_history_widget_en if lang == "en" 
                 else self.caption_history_widget_es)
        history_list = (self.caption_history_en if lang == "en" 
                       else self.caption_history_es)
        
        # Clear 'waiting' message if present
        if widget.get('1.0', tk.END).strip() == 'Waiting for speech...':
            widget.delete('1.0', tk.END)
        
        # Special handling for "..." preview
        if text == "...":
            widget.delete('1.0', tk.END)
            for caption, confidences in history_list:
                self.insert_colored_text(widget, caption, confidences)
                widget.insert(tk.END, '\n')  # New line after each finalized sentence
            widget.insert(tk.END, "...", 'preview')
            widget.see(tk.END)
            return
        
        # Filter low confidence words only for final text
        if is_final:
            filtered_text, filtered_confidences = self.filter_low_confidence_words(text, word_confidences)
        else:
            filtered_text, filtered_confidences = text, word_confidences
        
        if is_final:
            # Add to history
            history_list.append((filtered_text, filtered_confidences))
            
            if len(history_list) > self.max_history:
                history_list.pop(0)
        
        # Update display
        widget.delete('1.0', tk.END)
        
        # Show all history
        for i, (caption, confidences) in enumerate(history_list):
            self.insert_colored_text(widget, caption, confidences)
            widget.insert(tk.END, '\n')  # New line after each finalized sentence
        
        # Show current text
        if not is_final:
            self.insert_colored_text(widget, filtered_text, filtered_confidences, True)
        
        # Always scroll to see the latest text
        widget.see(tk.END)
        
        # Visual feedback
        self.status_label.config(fg='yellow')
        self.root.after(100, lambda: self.status_label.config(fg='green'))

        # Placeholder for custom language detection
        if is_final:
            # TODO: Implement custom language detection here
            # For now, we'll just use the 'lang' parameter
            if lang == 'en':
                self.current_language = "English"
            elif lang == 'es':
                self.current_language = "Spanish"
            else:
                self.current_language = "Unknown"
            
            self.language_indicator.config(text=f"Detected Language: {self.current_language}")

    def filter_low_confidence_words(self, text, confidences):
        # Filter out words with confidence below the threshold
        words = text.split()
        filtered_words = []
        filtered_confidences = []
        
        for word, confidence in zip(words, confidences):
            if confidence >= self.confidence_threshold:
                filtered_words.append(word)
                filtered_confidences.append(confidence)
        
        return ' '.join(filtered_words), filtered_confidences

    def insert_colored_text(self, widget, text, confidences, is_preview=False):
        # Insert text into widget with color coding based on confidence
        words = text.split()
        for i, word in enumerate(words):
            if confidences and i < len(confidences):
                confidence = confidences[i]
                if confidence >= 0.85:
                    tag = 'green'
                elif confidence >= 0.65:
                    tag = 'yellow'
                elif confidence >= 0.5:
                    tag = 'red'
                else:
                    tag = 'white'  # This case shouldn't occur for final text due to filtering
            else:
                tag = 'white'
            
            widget.insert(tk.END, word, tag)
            if i < len(words) - 1:  # Add space after every word except the last one
                widget.insert(tk.END, ' ', tag)
        
        if is_preview:
            widget.tag_add('preview', f"{widget.index(tk.END)} linestart", tk.END)

    def clear_history(self):
        # Clear all caption history
        for widget, lang in [(self.caption_history_widget_en, 'en'), 
                           (self.caption_history_widget_es, 'es')]:
            widget.delete('1.0', tk.END)
            widget.insert('1.0', 'Waiting for speech...')
            widget.tag_add('center', '1.0', 'end')
            widget.tag_add('waiting', '1.0', 'end')
        self.caption_history_en = []
        self.caption_history_es = []
        self.current_preview_en = None
        self.current_preview_es = None

    def change_audio_device(self, event=None):
        # Change the current audio input device
        selected_name = self.device_var.get()
        selected_index = next(i for i, device in self.available_devices 
                            if device[1] == selected_name)[0]
        
        if selected_index != self.current_device_index:
            self.current_device_index = selected_index
            self.restart_audio_stream()

    def restart_audio_stream(self):
        # Restart the audio stream with the new device
        try:
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()

            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=self.current_device_index,
                stream_callback=self.audio_callback
            )
            
            self.status_label.config(
                text=f"🎤 Active - {self.device_var.get()}", fg='green')
        except Exception as e:
            self.status_label.config(
                text=f"❌ Error: Could not open audio device", fg='red')
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        # Callback function for audio stream
        self.audio_queue.put(bytes(in_data))
        return (None, pyaudio.paContinue)
    
    def process_audio(self):
        current_sentence = {"en": "", "es": ""}
        current_confidences = {"en": [], "es": []}

        while True:
            data = self.audio_queue.get()
            if len(data) == 0:
                continue
            
            for lang, recognizer in self.recognizers.items():
                # Process final results
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get("text", ""):
                        final_text = current_sentence[lang] + " " + result["text"]
                        final_text = final_text.strip()
                        final_confidences = current_confidences[lang] + [word['conf'] for word in result.get('result', [])]
                        self.root.after(0, self.update_caption, 
                                      final_text, True, lang, final_confidences)
                        # Reset sentence tracking
                        current_sentence[lang] = ""
                        current_confidences[lang] = []
                
                # Process partial results
                partial = json.loads(recognizer.PartialResult())
                if partial.get("partial", ""):
                    words = partial["partial"].split()
                    word_confidences = [word['conf'] for word in partial.get('result', [])]
                    
                    if len(words) <= 4:
                        # Show "..." for the first 4 words
                        self.root.after(0, self.update_caption, "...", False, lang, [])
                    else:
                        # Update the current sentence
                        new_text = " ".join(words)
                        if new_text.startswith(current_sentence[lang]):
                            additional_text = new_text[len(current_sentence[lang]):].strip()
                            current_sentence[lang] = new_text
                            current_confidences[lang] = word_confidences
                        else:
                            additional_text = new_text
                            current_sentence[lang] = new_text
                            current_confidences[lang] = word_confidences
                        
                        # Update the display with the current sentence
                        self.root.after(0, self.update_caption, 
                                      current_sentence[lang], False, lang, current_confidences[lang])
    
    def on_closing(self):
        # Clean up and close the application
        self.caption_history_en = []
        self.caption_history_es = []
        self.root.destroy()
    
    def start_capturing(self):
        # Start the audio capture and processing
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=self.current_device_index,
                stream_callback=self.audio_callback
            )
            
            self.status_label.config(text="🎤 Active")
            
            processing_thread = threading.Thread(target=self.process_audio, daemon=True)
            processing_thread.start()
            
            self.root.mainloop()
            
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", fg='red')
            self.root.mainloop()

if __name__ == "__main__":
    captioner = LiveCaptioner()
    captioner.start_capturing()
