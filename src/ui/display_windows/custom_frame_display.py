"""
Custom Frame Display Window
Cho phép user định nghĩa frame structure
"""
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QVBoxLayout, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt
from .base_display import BaseDisplayWindow
from ...core.protocol_analyzer import CustomFrameAnalyzer, FrameDefinition
from ...core.data_parser import TimestampFormatter


class CustomFrameDisplayWindow(BaseDisplayWindow):
    """Display window cho custom frame definition"""
    
    def __init__(self, port: str, display_mode: str, frame_definition: FrameDefinition, parent=None):
        self.frame_definition = frame_definition
        self.analyzer = CustomFrameAnalyzer()
        self.analyzer.add_definition(frame_definition)
        self.table: QTableWidget = None
        self.row_count = 0
        
        super().__init__(port, display_mode, parent)
    
    def _setup_ui(self):
        """Override để thêm nút Edit Definition"""
        super()._setup_ui()
        
        # Thêm nút Edit Definition vào header
        layout = self.layout()
        header_layout = layout.itemAt(0).layout()
        
        edit_btn = QPushButton("Edit Definition")
        edit_btn.clicked.connect(self._on_edit_definition)
        header_layout.insertWidget(1, edit_btn)
    
    def _create_display_widget(self) -> QWidget:
        """Tạo QTableWidget để hiển thị custom frames"""
        self.table = QTableWidget()
        
        # Setup columns: Time, Dir, [Field columns], Valid, Raw Data
        field_names = [field['name'] for field in self.frame_definition.fields]
        columns = ["Time", "Dir"] + field_names + ["Valid", "Raw Data (HEX)"]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Dir
        
        # Field columns
        for i in range(len(field_names)):
            header.setSectionResizeMode(i + 2, QHeaderView.ResizeMode.Stretch)
        
        header.setSectionResizeMode(len(columns) - 2, QHeaderView.ResizeMode.ResizeToContents)  # Valid
        header.setSectionResizeMode(len(columns) - 1, QHeaderView.ResizeMode.Stretch)  # Raw Data
        
        return self.table
    
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """Hiển thị và parse custom frame"""
        if self.paused:
            return
        
        # Parse frame
        frame = self.analyzer.parse_frame(data, self.frame_definition.name)
        
        if frame is None:
            return
        
        # Format timestamp
        ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
        
        # Thêm row mới
        self.table.insertRow(self.row_count)
        
        col = 0
        
        # Time
        self.table.setItem(self.row_count, col, QTableWidgetItem(ts_str))
        col += 1
        
        # Direction
        dir_item = QTableWidgetItem("→" if direction == "TX" else "←")
        self.table.setItem(self.row_count, col, dir_item)
        col += 1
        
        # Field values
        for field in self.frame_definition.fields:
            field_name = field['name']
            value = frame.parsed_fields.get(field_name, "")
            
            # Format value
            if isinstance(value, bytes):
                value_str = value.hex()
            else:
                value_str = str(value)
            
            self.table.setItem(self.row_count, col, QTableWidgetItem(value_str))
            col += 1
        
        # Valid
        valid_item = QTableWidgetItem("✓" if frame.is_valid else "✗")
        if not frame.is_valid:
            valid_item.setForeground(Qt.GlobalColor.red)
        else:
            valid_item.setForeground(Qt.GlobalColor.green)
        self.table.setItem(self.row_count, col, valid_item)
        col += 1
        
        # Raw Data
        raw_hex = frame.raw_data.hex().upper()
        raw_item = QTableWidgetItem(raw_hex if len(raw_hex) < 50 else raw_hex[:50] + "...")
        self.table.setItem(self.row_count, col, raw_item)
        
        self.row_count += 1
        
        # Giới hạn số rows
        if self.row_count > self.max_lines:
            self.table.removeRow(0)
            self.row_count -= 1
        
        # Auto scroll
        if self.auto_scroll:
            self.table.scrollToBottom()
        
        # Update status
        self.line_count_label.setText(f"Frames: {self.row_count}")
        status = f"Last: {direction} at {ts_str}"
        if not frame.is_valid and frame.error_msg:
            status += f" | Error: {frame.error_msg}"
        self.status_label.setText(status)
    
    def clear_display(self):
        """Xóa tất cả rows"""
        self.table.setRowCount(0)
        self.row_count = 0
        self.line_count_label.setText("Frames: 0")
    
    def _on_edit_definition(self):
        """Mở dialog để edit frame definition"""
        # TODO: Implement frame definition editor dialog
        pass
