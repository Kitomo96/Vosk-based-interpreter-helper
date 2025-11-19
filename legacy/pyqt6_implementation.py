import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLabel, QSlider, QPushButton, 
                            QStatusBar, QFrame, QProgressBar, QComboBox)
from PyQt6.QtCore import Qt, QSettings, QPoint, QTimer
from PyQt6.QtGui import QCursor, QFont
import sounddevice as sd
import numpy as np

class ControlsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add audio input selector
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel('Input:'))
        self.input_selector = QComboBox()
        self.input_selector.setFixedWidth(140)
        input_layout.addWidget(self.input_selector)
        
        # Add other controls
        self.always_on_top_btn = QPushButton('📌 Always On Top')
        self.always_on_top_btn.setCheckable(True)
        
        # Transparency control
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel('Opacity:'))
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(50, 100)
        self.transparency_slider.setValue(100)
        opacity_layout.addWidget(self.transparency_slider)
        
        # Add widgets to layout
        layout.addLayout(input_layout)
        layout.addWidget(self.always_on_top_btn)
        layout.addLayout(opacity_layout)
        
        # Install event filters
        self.installEventFilter(self)
        self.input_selector.view().installEventFilter(self)
        
    def eventFilter(self, obj, event):
        if obj == self.input_selector.view():
            if event.type() == event.Type.Leave:
                self.input_selector.hidePopup()
        elif obj == self:
            if event.type() == event.Type.Leave:
                if not self.geometry().contains(self.mapFromGlobal(QCursor.pos())) and \
                   not self.input_selector.view().isVisible():
                    self.hide()
                    self.parent().controls_visible = False
        return super().eventFilter(obj, event)

class AudioManager:
    def __init__(self, controls_panel):
        self.sample_rate = 16000
        self.channels = 1
        self.device_info = None
        self.stream = None
        self.is_recording = False
        self.controls_panel = controls_panel
        self.is_muted = False
        
        # Initialize device list
        self.update_device_list()
        self.controls_panel.input_selector.currentIndexChanged.connect(self.change_input_device)

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f'Audio callback status: {status}')
        
        if self.is_muted:
            self.controls_panel.parent().audio_level.setValue(0)
            return
            
        audio_level = int(np.sqrt(np.mean(indata**2)) * 500)
        audio_level = min(100, max(0, audio_level))
        self.controls_panel.parent().audio_level.setValue(audio_level)

    def update_device_list(self):
        self.controls_panel.input_selector.clear()
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                name = f"{device['name']}"
                self.controls_panel.input_selector.addItem(name, i)
                
        default_device = sd.query_devices(kind='input')
        default_index = self.controls_panel.input_selector.findData(default_device['index'])
        if default_index >= 0:
            self.controls_panel.input_selector.setCurrentIndex(default_index)
    
    def change_input_device(self, index):
        if index < 0:
            return
            
        device_index = self.controls_panel.input_selector.currentData()
        print(f"Changing to device index: {device_index}")
        
        if self.stream:
            self.stop_stream()
            
        try:
            self.device_info = sd.query_devices(device_index, 'input')
            sd.default.device[0] = device_index
            print(f"Selected device: {self.device_info['name']}")
            self.start_stream()
        except sd.PortAudioError as e:
            print(f"Error changing device: {e}")
            
    def start_stream(self):
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self.audio_callback,
                dtype=np.float32
            )
            self.stream.start()
            self.is_recording = True
            print("Audio stream started successfully")
        except sd.PortAudioError as e:
            print(f"Error starting stream: {e}")
            
    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.is_recording = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('YourCompany', 'InterpreterAssistant')
        self.controls_visible = False
        self.initUI()
        self.loadSettings()
        
        # Initialize audio manager
        self.audio_manager = AudioManager(self.controls_panel)
        self.audio_manager.start_stream()

    def initUI(self):
        self.setWindowTitle('Interpreter Assistant')
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create controls panel
        self.controls_panel = ControlsPanel(self)
        self.controls_panel.always_on_top_btn.clicked.connect(self.toggle_always_on_top)
        self.controls_panel.transparency_slider.valueChanged.connect(self.update_transparency)

        # Create top button layout
        cog_layout = QHBoxLayout()
        cog_layout.addStretch()

        # Add mute button
        self.mute_btn = QPushButton('🎤')
        self.mute_btn.setFixedSize(30, 30)
        self.mute_btn.setCheckable(True)
        self.mute_btn.setToolTip('Mute/Unmute audio input')
        self.mute_btn.clicked.connect(self.update_mute_button)
        cog_layout.addWidget(self.mute_btn)

        # Add cog button
        self.cog_btn = QPushButton('⚙️')
        self.cog_btn.setFixedSize(30, 30)
        self.cog_btn.clicked.connect(self.show_controls)
        cog_layout.addWidget(self.cog_btn)
        cog_layout.setContentsMargins(5, 5, 5, 5)

        # Create audio level meter
        self.audio_level = QProgressBar()
        self.audio_level.setRange(0, 100)
        self.audio_level.setTextVisible(False)
        self.audio_level.setFixedHeight(2)
        self.audio_level.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: transparent;
                margin: 0px 5px;
            }
            QProgressBar::chunk {
                background-color: #8A2BE2;
                width: 1px;
            }
        """)

        # Create transcription panel
        self.transcription_panel = QTextEdit()
        self.transcription_panel.setReadOnly(True)
        self.transcription_panel.setFont(QFont('Arial', 12))

        # Add widgets to main layout
        main_layout.addLayout(cog_layout)
        main_layout.addWidget(self.audio_level)
        main_layout.addWidget(self.transcription_panel)

        # Create status bar with language indicator
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add permanent language indicator
        self.language_label = QLabel('Language: Not Detected')
        self.statusBar.addPermanentWidget(self.language_label)
        
        # Add ready message to the left side
        self.statusBar.showMessage('Ready')

    def toggle_always_on_top(self, checked):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()
        self.settings.setValue('always_on_top', checked)

    def show_controls(self):
        if self.controls_visible:
            self.controls_panel.hide()
            self.controls_visible = False
        else:
            button_pos = self.cog_btn.mapToGlobal(QPoint(0, 0))
            panel_x = button_pos.x() - self.controls_panel.sizeHint().width() + self.cog_btn.width()
            panel_y = button_pos.y() + self.cog_btn.height()
            self.controls_panel.move(panel_x, panel_y)
            self.controls_panel.show()
            self.controls_visible = True

    def update_transparency(self, value):
        self.setWindowOpacity(value / 100)
        self.settings.setValue('transparency', value)

    def update_mute_button(self):
        is_muted = self.mute_btn.isChecked()
        if is_muted:
            self.mute_btn.setText('🔇')
            self.mute_btn.setToolTip('Unmute audio input')
        else:
            self.mute_btn.setText('🎤')
            self.mute_btn.setToolTip('Mute audio input')
            
        if hasattr(self, 'audio_manager'):
            self.audio_manager.is_muted = is_muted
            print(f"Mute state changed to: {is_muted}")

    def loadSettings(self):
        self.controls_panel.always_on_top_btn.setChecked(
            self.settings.value('always_on_top', False, type=bool))
        self.toggle_always_on_top(self.controls_panel.always_on_top_btn.isChecked())

        saved_width = self.settings.value('window_width', 600, type=int)
        saved_height = self.settings.value('window_height', 400, type=int)
        self.resize(saved_width, saved_height)

        self.controls_panel.transparency_slider.setValue(
            self.settings.value('transparency', 100, type=int))

        is_muted = self.settings.value('is_muted', False, type=bool)
        self.mute_btn.setChecked(is_muted)
        self.update_mute_button()

    def closeEvent(self, event):
        if hasattr(self, 'audio_manager') and self.audio_manager.stream:
            self.audio_manager.stop_stream()
        self.settings.setValue('window_width', self.width())
        self.settings.setValue('window_height', self.height())
        self.settings.setValue('is_muted', self.mute_btn.isChecked())
        super().closeEvent(event)

    def update_language(self, language):
        """Update the detected language in the status bar"""
        self.language_label.setText(f'Language: {language}')

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()