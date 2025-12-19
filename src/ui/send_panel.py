"""
Send Panel - Panel để gửi dữ liệu qua serial
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QComboBox, QLabel, QCheckBox, 
                             QSpinBox, QGroupBox)
from PyQt6.QtCore import pyqtSignal, Qt
from ..core.data_parser import DataParser


class SendPanel(QWidget):
    """Panel để gửi dữ liệu"""
    
    # Signals
    send_data = pyqtSignal(bytes)
    connect_clicked = pyqtSignal()  # Signal khi click connect/disconnect
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.periodic_timer = None
        self.is_connected = False
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Top row: Connection + Input
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # Connection controls
        conn_widget = QWidget()
        conn_layout = QVBoxLayout(conn_widget)
        conn_layout.setContentsMargins(0, 0, 0, 0)
        conn_layout.setSpacing(2)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setCheckable(True)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.connect_btn.setMinimumWidth(100)
        self.connect_btn.setMaximumHeight(60)
        conn_layout.addWidget(self.connect_btn)
        
        self.conn_status_label = QLabel("Disconnected")
        self.conn_status_label.setStyleSheet("color: #888; font-size: 9pt;")
        self.conn_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        conn_layout.addWidget(self.conn_status_label)
        
        top_layout.addWidget(conn_widget)
        
        # Input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(2)
        
        # Format and Line ending in one row
        format_layout = QHBoxLayout()
        format_layout.setSpacing(5)
        
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["ASCII", "HEX", "Decimal", "Binary"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        format_layout.addWidget(QLabel("Line End:"))
        self.line_ending_combo = QComboBox()
        self.line_ending_combo.addItem("None", "")
        self.line_ending_combo.addItem("\\n", "\n")
        self.line_ending_combo.addItem("\\r", "\r")
        self.line_ending_combo.addItem("\\r\\n", "\r\n")
        format_layout.addWidget(self.line_ending_combo)
        
        format_layout.addStretch()
        input_layout.addLayout(format_layout)
        
        # Input text area - compact
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(50)
        self.input_text.setPlaceholderText("Enter data...")
        input_layout.addWidget(self.input_text)
        
        # Format hint
        self.format_hint = QLabel("Format: Type ASCII text")
        self.format_hint.setStyleSheet("color: #888; font-size: 8pt;")
        input_layout.addWidget(self.format_hint)
        
        top_layout.addWidget(input_widget, stretch=1)
        
        layout.addLayout(top_layout)
        
        # Bottom row: Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.send_btn.setMinimumWidth(80)
        button_layout.addWidget(self.send_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.input_text.clear)
        self.clear_btn.setMinimumWidth(60)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        
        # Periodic send
        self.periodic_cb = QCheckBox("Periodic")
        self.periodic_cb.stateChanged.connect(self._on_periodic_toggled)
        button_layout.addWidget(self.periodic_cb)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 999999)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSingleStep(100)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.setMaximumWidth(100)
        button_layout.addWidget(self.interval_spin)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; font-size: 9pt;")
        button_layout.addWidget(self.status_label)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setMaximumHeight(150)  # Giới hạn chiều cao
    
    def _on_format_changed(self, format_text: str):
        """Thay đổi format"""
        hints = {
            "ASCII": "Format: Type ASCII text",
            "HEX": "Format: Enter hex bytes (e.g., 01 02 03 or 010203)",
            "Decimal": "Format: Enter decimal bytes separated by space (e.g., 65 66 67)",
            "Binary": "Format: Enter binary bytes separated by space (e.g., 01000001 01000010)"
        }
        self.format_hint.setText(hints.get(format_text, ""))
    
    def _on_connect_clicked(self, checked: bool):
        """Xử lý khi click nút Connect/Disconnect"""
        self.connect_clicked.emit()
    
    def set_connection_state(self, connected: bool, port_name: str = ""):
        """Cập nhật trạng thái kết nối"""
        self.is_connected = connected
        
        if connected:
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setChecked(True)
            self.conn_status_label.setText(f"Connected to {port_name}")
            self.conn_status_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
            self.set_send_enabled(True)
        else:
            self.connect_btn.setText("Connect")
            self.connect_btn.setChecked(False)
            self.conn_status_label.setText("Disconnected")
            self.conn_status_label.setStyleSheet("color: #888;")
            self.set_send_enabled(False)
    
    def _on_send_clicked(self):
        """Gửi dữ liệu"""
        text = self.input_text.toPlainText()
        if not text:
            self.status_label.setText("Error: No data to send")
            return
        
        try:
            data = self._parse_input(text)
            if data:
                self.send_data.emit(data)
                self.status_label.setText(f"Sent: {len(data)} bytes")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def _parse_input(self, text: str) -> bytes:
        """Parse input text theo format"""
        format_type = self.format_combo.currentText()
        
        # Get line ending
        line_ending = self.line_ending_combo.currentData()
        if line_ending:
            text = text + line_ending
        
        if format_type == "ASCII":
            return text.encode('utf-8')
        
        elif format_type == "HEX":
            # Remove spaces and convert
            hex_str = text.replace(" ", "").replace("\n", "").replace("\r", "")
            return DataParser.hex_string_to_bytes(hex_str)
        
        elif format_type == "Decimal":
            # Parse decimal numbers
            numbers = text.replace("\n", " ").replace("\r", " ").split()
            byte_list = [int(n) & 0xFF for n in numbers if n.strip()]
            return bytes(byte_list)
        
        elif format_type == "Binary":
            # Parse binary numbers
            numbers = text.replace("\n", " ").replace("\r", " ").split()
            byte_list = [int(n, 2) & 0xFF for n in numbers if n.strip()]
            return bytes(byte_list)
        
        return b''
    
    def _on_periodic_toggled(self, state: int):
        """Toggle periodic send"""
        from PyQt6.QtCore import QTimer, Qt
        
        if state == Qt.CheckState.Checked.value:
            # Start periodic send
            if self.periodic_timer is None:
                self.periodic_timer = QTimer(self)
                self.periodic_timer.timeout.connect(self._on_send_clicked)
            
            interval = self.interval_spin.value()
            self.periodic_timer.start(interval)
            self.status_label.setText(f"Periodic send: every {interval}ms")
            
            # Disable interval spinbox
            self.interval_spin.setEnabled(False)
        else:
            # Stop periodic send
            if self.periodic_timer:
                self.periodic_timer.stop()
            
            self.status_label.setText("Periodic send stopped")
            self.interval_spin.setEnabled(True)
    
    def _apply_style(self):
        """Apply style"""
        # Don't apply inline style - let main theme handle it
        pass
    
    def set_send_enabled(self, enabled: bool):
        """Enable/disable send controls"""
        self.send_btn.setEnabled(enabled)
        self.input_text.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.line_ending_combo.setEnabled(enabled)
        
        if not enabled:
            self.periodic_cb.setChecked(False)
            self.periodic_cb.setEnabled(False)
        else:
            self.periodic_cb.setEnabled(True)
