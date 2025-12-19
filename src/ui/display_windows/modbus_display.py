"""
Modbus RTU Display Window
"""
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from .base_display import BaseDisplayWindow
from ...core.protocol_analyzer import ModbusRTUAnalyzer
from ...core.data_parser import TimestampFormatter


class ModbusDisplayWindow(BaseDisplayWindow):
    """Display window cho Modbus RTU protocol"""
    
    def __init__(self, port: str, display_mode: str, parent=None):
        self.table: QTableWidget = None
        self.row_count = 0
        super().__init__(port, display_mode, parent)
    
    def _create_display_widget(self) -> QWidget:
        """Tạo QTableWidget để hiển thị Modbus frames"""
        self.table = QTableWidget()
        
        # Setup columns
        columns = ["Time", "Dir", "Slave ID", "Function", "Data Len", "Data (HEX)", "CRC", "Valid", "Details"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Dir
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Slave ID
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Function
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Data Len
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Data
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # CRC
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Valid
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)  # Details
        
        return self.table
    
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """Hiển thị và phân tích Modbus frame"""
        if self.paused:
            return
        
        # Parse Modbus frame
        frame = ModbusRTUAnalyzer.parse_frame(data)
        
        if frame is None:
            # Không phải Modbus frame hợp lệ
            return
        
        # Analyze frame để lấy details
        analyzed = ModbusRTUAnalyzer.analyze_frame(frame)
        
        # Format timestamp
        ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
        
        # Thêm row mới
        self.table.insertRow(self.row_count)
        
        # Time
        self.table.setItem(self.row_count, 0, QTableWidgetItem(ts_str))
        
        # Direction
        dir_item = QTableWidgetItem("→" if direction == "TX" else "←")
        self.table.setItem(self.row_count, 1, dir_item)
        
        # Slave ID
        self.table.setItem(self.row_count, 2, QTableWidgetItem(str(frame.slave_id)))
        
        # Function
        func_item = QTableWidgetItem(analyzed['function_name'])
        self.table.setItem(self.row_count, 3, func_item)
        
        # Data Length
        self.table.setItem(self.row_count, 4, QTableWidgetItem(str(len(frame.data))))
        
        # Data (HEX)
        data_hex = analyzed['data_hex']
        data_item = QTableWidgetItem(data_hex if len(data_hex) < 50 else data_hex[:50] + "...")
        self.table.setItem(self.row_count, 5, data_item)
        
        # CRC
        crc_item = QTableWidgetItem(analyzed['crc'])
        self.table.setItem(self.row_count, 6, crc_item)
        
        # Valid
        valid_item = QTableWidgetItem("✓" if frame.is_valid else "✗")
        if not frame.is_valid:
            valid_item.setForeground(Qt.GlobalColor.red)
        else:
            valid_item.setForeground(Qt.GlobalColor.green)
        self.table.setItem(self.row_count, 7, valid_item)
        
        # Details
        details_str = ""
        if 'details' in analyzed:
            details = analyzed['details']
            if 'type' in details:
                details_str = details['type']
                if 'start_address' in details:
                    details_str += f" @ {details['start_address']}"
                if 'quantity' in details:
                    details_str += f" ({details['quantity']})"
                if 'registers' in details:
                    details_str += f" = {details['registers']}"
        
        if frame.error_msg:
            details_str = frame.error_msg
        
        details_item = QTableWidgetItem(details_str)
        self.table.setItem(self.row_count, 8, details_item)
        
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
        self.status_label.setText(f"Last: {direction} at {ts_str}")
    
    def clear_display(self):
        """Xóa tất cả rows"""
        self.table.setRowCount(0)
        self.row_count = 0
        self.line_count_label.setText("Frames: 0")
