"""
Decimal Display Window
"""
from datetime import datetime
from .base_display import TextBasedDisplayWindow
from ...core.data_parser import DataParser, TimestampFormatter


class DecimalDisplayWindow(TextBasedDisplayWindow):
    """Display window cho Decimal format"""
    
    def __init__(self, port: str, display_mode: str, parent=None):
        super().__init__(port, display_mode, parent)
    
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """Hiển thị dữ liệu Decimal"""
        # Convert to Decimal
        decimal_str = DataParser.bytes_to_decimal(data, separator=" ")
        
        # Format với timestamp
        ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
        direction_marker = "→" if direction == "TX" else "←"
        
        # Màu sắc theo direction
        color = "#4ec9b0" if direction == "TX" else "#ce9178"
        
        line = f"[{ts_str}] {direction_marker} {decimal_str}"
        
        self.append_text(line, color)
        self.status_label.setText(f"Last: {direction} at {ts_str}")
