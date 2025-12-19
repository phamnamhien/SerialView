"""
Helper functions - Các hàm tiện ích dùng chung
"""
import os
import json
from typing import Any, List, Dict
from datetime import datetime


def ensure_dir(directory: str):
    """Đảm bảo thư mục tồn tại"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_json(filepath: str, data: Dict[str, Any]):
    """Lưu dữ liệu vào JSON file"""
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_json(filepath: str) -> Dict[str, Any]:
    """Load dữ liệu từ JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_bytes_size(size_bytes: int) -> str:
    """Format kích thước file theo KB, MB, GB"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_timestamp_string(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """Lấy timestamp string cho filename"""
    return datetime.now().strftime(fmt)


def sanitize_filename(filename: str) -> str:
    """Làm sạch filename, loại bỏ ký tự không hợp lệ"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Chia list thành các chunk nhỏ hơn"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def bytes_to_hex_dump(data: bytes, bytes_per_line: int = 16) -> str:
    """Tạo hex dump string giống hexdump command"""
    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        
        # Offset
        offset = f"{i:08x}"
        
        # Hex bytes
        hex_part = ' '.join(f"{b:02x}" for b in chunk)
        hex_part = hex_part.ljust(bytes_per_line * 3 - 1)
        
        # ASCII part
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        
        lines.append(f"{offset}  {hex_part}  |{ascii_part}|")
    
    return '\n'.join(lines)


class RingBuffer:
    """Ring buffer cho lưu data với kích thước cố định"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.buffer = []
    
    def append(self, item: Any):
        """Thêm item vào buffer"""
        self.buffer.append(item)
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)
    
    def get_all(self) -> List[Any]:
        """Lấy tất cả items"""
        return self.buffer.copy()
    
    def clear(self):
        """Xóa buffer"""
        self.buffer.clear()
    
    def __len__(self):
        return len(self.buffer)
    
    def __getitem__(self, index):
        return self.buffer[index]
