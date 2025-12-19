"""
Mixed Display Window (HEX + ASCII)
"""
from datetime import datetime
from .base_display import TextBasedDisplayWindow
from ...core.data_parser import DataParser, TimestampFormatter


class MixedDisplayWindow(TextBasedDisplayWindow):
    """Display window cho Mixed format (HEX + ASCII)"""
    
    def __init__(self, port: str, display_mode: str, parent=None):
        super().__init__(port, display_mode, parent)
    
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """Hiển thị dữ liệu Mixed format"""
        # Convert to Mixed
        mixed_str = DataParser.bytes_to_mixed(data, bytes_per_line=16)
        
        # Format với timestamp và direction
        ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
        direction_marker = "→" if direction == "TX" else "←"
        
        # Màu sắc theo direction
        color = "#4ec9b0" if direction == "TX" else "#ce9178"
        
        header = f"[{ts_str}] {direction_marker} ({len(data)} bytes)"
        
        # Thêm header và mixed data với màu
        self.append_text(header, color)
        self.append_text(mixed_str, color)
        self.append_text("")  # Dòng trống
        
        self.status_label.setText(f"Last: {direction} at {ts_str}")
