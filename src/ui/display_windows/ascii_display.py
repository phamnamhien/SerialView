"""
ASCII Display Window with Line Buffering
Handles incomplete lines from serial data
"""
from datetime import datetime
from .base_display import TextBasedDisplayWindow
from ...core.data_parser import DataParser, TimestampFormatter


class AsciiDisplayWindow(TextBasedDisplayWindow):
    """Display window for ASCII format with line buffering"""
    
    def __init__(self, port: str, display_mode: str, parent=None):
        super().__init__(port, display_mode, parent)
        self.line_buffer = b''  # Buffer for incomplete lines
    
    def display_data(self, data: bytes, timestamp: datetime, direction: str):
        """Display ASCII data with line buffering"""
        # Add to buffer
        self.line_buffer += data
        
        # Color based on direction
        color = "#4ec9b0" if direction == "TX" else "#ce9178"
        
        # Format timestamp
        ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
        direction_marker = "→" if direction == "TX" else "←"
        
        # Split by newline
        while b'\n' in self.line_buffer:
            # Find first newline
            pos = self.line_buffer.find(b'\n')
            line_data = self.line_buffer[:pos]
            self.line_buffer = self.line_buffer[pos+1:]  # Remove processed part
            
            # Convert to ASCII
            ascii_str = DataParser.bytes_to_ascii(line_data, replace_non_printable=True)
            
            # Remove \r if exists
            ascii_str = ascii_str.rstrip('\r')
            
            # Display complete line
            formatted_line = f"[{ts_str}] {direction_marker} {ascii_str}"
            self.append_text(formatted_line, color)
        
        # If buffer too large without newline, flush it
        if len(self.line_buffer) > 1000:
            ascii_str = DataParser.bytes_to_ascii(self.line_buffer, replace_non_printable=True)
            formatted_line = f"[{ts_str}] {direction_marker} {ascii_str}"
            self.append_text(formatted_line, color)
            self.line_buffer = b''
        
        self.status_label.setText(f"Last: {direction} at {ts_str}")