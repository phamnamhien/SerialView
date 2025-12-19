"""
HEX Display Window
"""
from datetime import datetime
from .base_display import TextBasedDisplayWindow
from ...core.data_parser import DataParser, TimestampFormatter


class HexDisplayWindow(TextBasedDisplayWindow):
    """Display window cho HEX format"""
    
    def __init__(self, port: str, display_mode: str, parent=None):
        super().__init__(port, display_mode, parent)
    
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """Hiển thị dữ liệu HEX"""
        # Convert to HEX
        hex_str = DataParser.bytes_to_hex(data, separator=" ", uppercase=True)
        
        # Format với timestamp
        ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
        direction_marker = "→" if direction == "TX" else "←"
        
        # Màu sắc theo direction
        color = "#4ec9b0" if direction == "TX" else "#ce9178"  # TX: cyan, RX: orange
        
        line = f"[{ts_str}] {direction_marker} {hex_str}"
        
        self.append_text(line, color)
        self.status_label.setText(f"Last: {direction} at {ts_str} ({len(data)} bytes)")
