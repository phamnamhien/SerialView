"""
ASCII Display Window
"""
from datetime import datetime
from .base_display import TextBasedDisplayWindow
from ...core.data_parser import DataParser, TimestampFormatter


class AsciiDisplayWindow(TextBasedDisplayWindow):
    """Display window cho ASCII format"""
    
    def __init__(self, port: str, display_mode: str, parent=None):
        super().__init__(port, display_mode, parent)
    
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """Hiển thị dữ liệu ASCII - mỗi packet hiển thị ngay"""
        # Convert to ASCII (giữ \n, bỏ \r)
        ascii_str = DataParser.bytes_to_ascii(data, replace_non_printable=True)
        
        # Format timestamp
        ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
        direction_marker = "→" if direction == "TX" else "←"
        
        # Màu sắc theo direction
        color = "#4ec9b0" if direction == "TX" else "#ce9178"  # TX: cyan, RX: orange
        
        # Hiển thị ngay lập tức - mỗi data packet là 1 dòng
        # Nếu có nhiều dòng (có \n), giữ nguyên format
        lines = ascii_str.split('\n')
        
        for i, line in enumerate(lines):
            # Skip empty lines ở cuối (do kết thúc bằng \n)
            if i == len(lines) - 1 and not line:
                continue
            
            formatted_line = f"[{ts_str}] {direction_marker} {line}"
            self.append_text(formatted_line, color)
        
        self.status_label.setText(f"Last: {direction} at {ts_str}")
