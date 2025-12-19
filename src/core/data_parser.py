"""
Data Parser - Chuyển đổi giữa các format hiển thị
ASCII, HEX, Binary, Decimal, Timestamp
"""
from typing import List, Union
from datetime import datetime
from enum import Enum


class DisplayFormat(Enum):
    """Các format hiển thị"""
    ASCII = "ASCII"
    HEX = "HEX"
    BINARY = "Binary"
    DECIMAL = "Decimal"
    MIXED = "Mixed"  # Hiển thị cả ASCII và HEX


class DataParser:
    """Parser dữ liệu serial"""
    
    @staticmethod
    def bytes_to_ascii(data: bytes, replace_non_printable: bool = True) -> str:
        """
        Chuyển bytes sang ASCII
        Args:
            data: dữ liệu bytes
            replace_non_printable: thay thế ký tự không hiển thị được bằng '.'
        """
        if replace_non_printable:
            result = []
            for byte in data:
                if 32 <= byte <= 126:  # Printable ASCII
                    result.append(chr(byte))
                elif byte == 0x0A:  # Line Feed (LF) \n
                    result.append('\n')
                elif byte == 0x0D:  # Carriage Return (CR) \r
                    # Skip CR, chỉ giữ LF để tránh hiển thị lộn xộn
                    continue
                elif byte == 0x09:  # Tab
                    result.append('\t')
                else:
                    result.append('.')
            return ''.join(result)
        else:
            try:
                return data.decode('ascii', errors='replace')
            except:
                return data.decode('utf-8', errors='replace')
    
    @staticmethod
    def bytes_to_hex(data: bytes, separator: str = " ", uppercase: bool = True,
                     show_address: bool = False, bytes_per_line: int = 16) -> str:
        """
        Chuyển bytes sang HEX
        Args:
            data: dữ liệu bytes
            separator: ký tự phân cách giữa các byte
            uppercase: hiển thị chữ hoa
            show_address: hiển thị địa chỉ offset
            bytes_per_line: số byte mỗi dòng (nếu show_address=True)
        """
        if not data:
            return ""
        
        hex_format = "{:02X}" if uppercase else "{:02x}"
        
        if show_address:
            lines = []
            for i in range(0, len(data), bytes_per_line):
                chunk = data[i:i + bytes_per_line]
                hex_str = separator.join(hex_format.format(b) for b in chunk)
                ascii_str = DataParser.bytes_to_ascii(chunk, replace_non_printable=True)
                line = f"{i:08X}: {hex_str:<{bytes_per_line*3}}  {ascii_str}"
                lines.append(line)
            return '\n'.join(lines)
        else:
            return separator.join(hex_format.format(b) for b in data)
    
    @staticmethod
    def bytes_to_binary(data: bytes, separator: str = " ", bytes_per_line: int = 8) -> str:
        """
        Chuyển bytes sang Binary
        Args:
            data: dữ liệu bytes
            separator: ký tự phân cách
            bytes_per_line: số byte mỗi dòng
        """
        if not data:
            return ""
        
        binary_strs = [f"{b:08b}" for b in data]
        
        if bytes_per_line:
            lines = []
            for i in range(0, len(binary_strs), bytes_per_line):
                chunk = binary_strs[i:i + bytes_per_line]
                lines.append(separator.join(chunk))
            return '\n'.join(lines)
        else:
            return separator.join(binary_strs)
    
    @staticmethod
    def bytes_to_decimal(data: bytes, separator: str = " ", bytes_per_line: int = 16) -> str:
        """
        Chuyển bytes sang Decimal
        Args:
            data: dữ liệu bytes
            separator: ký tự phân cách
            bytes_per_line: số byte mỗi dòng
        """
        if not data:
            return ""
        
        decimal_strs = [f"{b:3d}" for b in data]
        
        if bytes_per_line:
            lines = []
            for i in range(0, len(decimal_strs), bytes_per_line):
                chunk = decimal_strs[i:i + bytes_per_line]
                lines.append(separator.join(chunk))
            return '\n'.join(lines)
        else:
            return separator.join(decimal_strs)
    
    @staticmethod
    def bytes_to_mixed(data: bytes, bytes_per_line: int = 16) -> str:
        """
        Hiển thị mixed format (HEX + ASCII)
        Format giống hex editor
        """
        if not data:
            return ""
        
        lines = []
        for i in range(0, len(data), bytes_per_line):
            chunk = data[i:i + bytes_per_line]
            
            # HEX part
            hex_str = ' '.join(f"{b:02X}" for b in chunk)
            
            # ASCII part
            ascii_str = DataParser.bytes_to_ascii(chunk, replace_non_printable=True)
            
            # Format: offset | hex bytes | ascii
            line = f"{i:08X} | {hex_str:<{bytes_per_line*3}} | {ascii_str}"
            lines.append(line)
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_with_timestamp(data_str: str, timestamp: datetime, 
                             direction: str, timestamp_format: str = "%H:%M:%S.%f") -> str:
        """
        Thêm timestamp và direction vào data
        Args:
            data_str: chuỗi dữ liệu đã format
            timestamp: timestamp
            direction: 'TX' hoặc 'RX'
            timestamp_format: format của timestamp
        """
        ts_str = timestamp.strftime(timestamp_format)[:-3]  # bỏ 3 số cuối của microsecond
        direction_marker = "→" if direction == "TX" else "←"
        return f"[{ts_str}] {direction_marker} {data_str}"
    
    @staticmethod
    def hex_string_to_bytes(hex_str: str) -> bytes:
        """
        Chuyển hex string sang bytes
        Hỗ trợ nhiều format: "01 02 03", "010203", "0x01 0x02"
        """
        # Loại bỏ whitespace và 0x prefix
        hex_str = hex_str.replace(" ", "").replace("0x", "").replace("0X", "")
        
        # Đảm bảo độ dài chẵn
        if len(hex_str) % 2 != 0:
            hex_str = "0" + hex_str
        
        try:
            return bytes.fromhex(hex_str)
        except ValueError as e:
            raise ValueError(f"Invalid hex string: {e}")
    
    @staticmethod
    def escape_string_to_bytes(s: str) -> bytes:
        """
        Chuyển string có escape sequences sang bytes
        VD: "Hello\\r\\n" -> b'Hello\r\n'
        """
        # Python's encode với unicode_escape
        return s.encode('utf-8').decode('unicode_escape').encode('latin1')
    
    @staticmethod
    def parse_input(input_str: str, input_format: str = "auto") -> bytes:
        """
        Parse input string theo format
        Args:
            input_str: chuỗi input
            input_format: "auto", "ascii", "hex", "escape"
        Returns:
            bytes data
        """
        if input_format == "hex":
            return DataParser.hex_string_to_bytes(input_str)
        elif input_format == "escape":
            return DataParser.escape_string_to_bytes(input_str)
        elif input_format == "ascii":
            return input_str.encode('utf-8')
        else:  # auto detect
            # Nếu toàn bộ là hex (với hoặc không space)
            test_str = input_str.replace(" ", "").replace("0x", "")
            if all(c in '0123456789ABCDEFabcdef' for c in test_str):
                return DataParser.hex_string_to_bytes(input_str)
            else:
                # Mặc định là ASCII
                return input_str.encode('utf-8')


class TimestampFormatter:
    """Format timestamp cho display"""
    
    @staticmethod
    def get_current_timestamp() -> datetime:
        """Lấy timestamp hiện tại"""
        return datetime.now()
    
    @staticmethod
    def format_timestamp(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S.%f") -> str:
        """Format datetime object"""
        return dt.strftime(format_str)[:-3]  # Bỏ 3 số cuối microsecond
    
    @staticmethod
    def format_duration(start: datetime, end: datetime = None) -> str:
        """Format khoảng thời gian"""
        if end is None:
            end = datetime.now()
        
        duration = end - start
        
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
