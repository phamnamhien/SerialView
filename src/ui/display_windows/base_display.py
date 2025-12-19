"""
Base Display Window - Abstract base class cho tất cả display windows
Implements singleton pattern per port per mode
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QCheckBox, QSpinBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextCursor
from datetime import datetime
from typing import Optional, Dict
from abc import ABCMeta, abstractmethod


class QWidgetABCMeta(type(QWidget), ABCMeta):
    """Metaclass để kết hợp QWidget và ABC"""
    pass


class BaseDisplayWindow(QWidget, metaclass=QWidgetABCMeta):
    """Base class cho tất cả display windows"""
    
    # Signals
    closed = pyqtSignal(str, str)  # port, display_mode
    
    # Class variable để track các instances (singleton per port per mode)
    _instances: Dict[tuple, 'BaseDisplayWindow'] = {}
    
    def __init__(self, port: str, display_mode: str, parent=None):
        super().__init__(parent)
        
        self.port = port
        self.display_mode = display_mode
        self.auto_scroll = True
        self.max_lines = 10000
        self.paused = False
        
        self._setup_ui()
        self._apply_style()
    
    @classmethod
    def get_instance(cls, port: str, display_mode: str, *args, **kwargs) -> Optional['BaseDisplayWindow']:
        """
        Lấy hoặc tạo instance (singleton per port per mode)
        Trả về None nếu instance đã tồn tại
        """
        key = (port, display_mode)
        
        if key in cls._instances:
            # Instance đã tồn tại, không cho tạo mới
            return None
        
        # Tạo instance mới
        instance = cls(port, display_mode, *args, **kwargs)
        cls._instances[key] = instance
        
        return instance
    
    @classmethod
    def remove_instance(cls, port: str, display_mode: str):
        """Xóa instance khỏi registry"""
        key = (port, display_mode)
        if key in cls._instances:
            del cls._instances[key]
    
    def _setup_ui(self):
        """Setup UI cơ bản"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(f"{self.display_mode} - {self.port}")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Controls
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setCheckable(True)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        header_layout.addWidget(self.pause_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_display)
        header_layout.addWidget(self.clear_btn)
        
        self.auto_scroll_cb = QCheckBox("Auto Scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.stateChanged.connect(self._on_auto_scroll_changed)
        header_layout.addWidget(self.auto_scroll_cb)
        
        layout.addLayout(header_layout)
        
        # Display area
        self.display_widget = self._create_display_widget()
        layout.addWidget(self.display_widget)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.line_count_label = QLabel("Lines: 0")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.line_count_label)
        
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
        
        # Set window properties
        self.setWindowTitle(f"{self.display_mode} - {self.port}")
        self.resize(800, 600)
    
    @abstractmethod
    def _create_display_widget(self) -> QWidget:
        """
        Tạo widget hiển thị chính (phải implement trong subclass)
        VD: QTextEdit cho ASCII, QTableWidget cho Modbus...
        """
        pass
    
    @abstractmethod
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """
        Hiển thị dữ liệu (phải implement trong subclass)
        Args:
            data: dữ liệu bytes
            timestamp: thời gian nhận/gửi
            direction: 'TX' hoặc 'RX'
        """
        pass
    
    @abstractmethod
    def clear_display(self):
        """Xóa display (phải implement trong subclass)"""
        pass
    
    def _on_pause_clicked(self, checked: bool):
        """Xử lý nút pause"""
        self.paused = checked
        self.pause_btn.setText("Resume" if checked else "Pause")
        self.status_label.setText("Paused" if checked else "Running")
    
    def _on_auto_scroll_changed(self, state: int):
        """Xử lý checkbox auto scroll"""
        self.auto_scroll = (state == Qt.CheckState.Checked.value)
    
    def _apply_style(self):
        """Áp dụng dark theme style"""
        # Don't apply style here - let main window theme handle it
        pass
    
    def closeEvent(self, event):
        """Override closeEvent để cleanup"""
        self.closed.emit(self.port, self.display_mode)
        BaseDisplayWindow.remove_instance(self.port, self.display_mode)
        event.accept()


class TextBasedDisplayWindow(BaseDisplayWindow):
    """Base class cho các display dạng text (ASCII, HEX, Binary...)"""
    
    def __init__(self, port: str, display_mode: str, parent=None):
        self.text_edit: Optional[QTextEdit] = None
        self.line_count = 0
        super().__init__(port, display_mode, parent)
    
    def _create_display_widget(self) -> QWidget:
        """Tạo QTextEdit widget"""
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        # Set font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        
        return self.text_edit
    
    def append_text(self, text: str, color: str = None):
        """Thêm text vào display với màu sắc tùy chọn"""
        if self.paused:
            return
        
        # Giới hạn số dòng
        if self.line_count >= self.max_lines:
            # Xóa dòng đầu tiên
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Xóa newline
        else:
            self.line_count += 1
        
        # Thêm text mới với màu
        if color:
            # Save current format
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            
            # Set color
            format = cursor.charFormat()
            from PyQt6.QtGui import QColor
            format.setForeground(QColor(color))
            
            cursor.setCharFormat(format)
            cursor.insertText(text + '\n')
            
            # Reset format
            format.setForeground(QColor("#d4d4d4"))  # Default color
            cursor.setCharFormat(format)
        else:
            self.text_edit.append(text)
        
        # Auto scroll
        if self.auto_scroll:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_edit.setTextCursor(cursor)
        
        # Update line count
        self.line_count_label.setText(f"Lines: {self.line_count}")
    
    def clear_display(self):
        """Xóa display"""
        if self.text_edit:
            self.text_edit.clear()
            self.line_count = 0
            self.line_count_label.setText("Lines: 0")
