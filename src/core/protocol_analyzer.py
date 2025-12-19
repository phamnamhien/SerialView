"""
Protocol Analyzer - Phân tích các giao thức
- Modbus RTU
- Custom Frame (user-defined)
"""
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import struct


class ModbusFunction(Enum):
    """Modbus function codes"""
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10


@dataclass
class ModbusFrame:
    """Modbus RTU Frame"""
    slave_id: int
    function_code: int
    data: bytes
    crc: int
    is_valid: bool
    error_msg: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển sang dictionary để hiển thị"""
        func_name = "Unknown"
        try:
            func_name = ModbusFunction(self.function_code).name
        except ValueError:
            func_name = f"Unknown (0x{self.function_code:02X})"
        
        return {
            'slave_id': self.slave_id,
            'function_code': f"0x{self.function_code:02X}",
            'function_name': func_name,
            'data_length': len(self.data),
            'data_hex': ' '.join(f"{b:02X}" for b in self.data),
            'crc': f"0x{self.crc:04X}",
            'is_valid': self.is_valid,
            'error_msg': self.error_msg
        }


@dataclass
class CustomFrame:
    """Custom Frame (user-defined)"""
    raw_data: bytes
    parsed_fields: Dict[str, Any]
    is_valid: bool
    error_msg: Optional[str] = None


class ModbusRTUAnalyzer:
    """Analyzer cho Modbus RTU protocol"""
    
    @staticmethod
    def calculate_crc(data: bytes) -> int:
        """Tính CRC16 Modbus"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    @staticmethod
    def parse_frame(data: bytes) -> Optional[ModbusFrame]:
        """
        Parse Modbus RTU frame
        Format: [Slave ID][Function][Data...][CRC Low][CRC High]
        """
        if len(data) < 4:  # Minimum frame: slave + function + 2 bytes CRC
            return None
        
        slave_id = data[0]
        function_code = data[1]
        frame_data = data[2:-2]
        received_crc = struct.unpack('<H', data[-2:])[0]  # Little-endian
        
        # Tính CRC
        calculated_crc = ModbusRTUAnalyzer.calculate_crc(data[:-2])
        is_valid = (received_crc == calculated_crc)
        
        error_msg = None
        if not is_valid:
            error_msg = f"CRC mismatch: received=0x{received_crc:04X}, calculated=0x{calculated_crc:04X}"
        
        return ModbusFrame(
            slave_id=slave_id,
            function_code=function_code,
            data=frame_data,
            crc=received_crc,
            is_valid=is_valid,
            error_msg=error_msg
        )
    
    @staticmethod
    def parse_read_holding_registers_request(frame: ModbusFrame) -> Dict[str, Any]:
        """Parse request đọc holding registers (function 0x03)"""
        if len(frame.data) < 4:
            return {'error': 'Invalid data length'}
        
        start_address = struct.unpack('>H', frame.data[0:2])[0]
        quantity = struct.unpack('>H', frame.data[2:4])[0]
        
        return {
            'type': 'Read Holding Registers Request',
            'start_address': start_address,
            'quantity': quantity
        }
    
    @staticmethod
    def parse_read_holding_registers_response(frame: ModbusFrame) -> Dict[str, Any]:
        """Parse response đọc holding registers"""
        if len(frame.data) < 1:
            return {'error': 'Invalid data length'}
        
        byte_count = frame.data[0]
        registers_data = frame.data[1:]
        
        if len(registers_data) != byte_count:
            return {'error': 'Byte count mismatch'}
        
        # Parse registers (mỗi register 2 bytes, big-endian)
        registers = []
        for i in range(0, len(registers_data), 2):
            if i + 1 < len(registers_data):
                reg_value = struct.unpack('>H', registers_data[i:i+2])[0]
                registers.append(reg_value)
        
        return {
            'type': 'Read Holding Registers Response',
            'byte_count': byte_count,
            'registers': registers,
            'registers_hex': [f"0x{r:04X}" for r in registers]
        }
    
    @staticmethod
    def parse_write_single_register_request(frame: ModbusFrame) -> Dict[str, Any]:
        """Parse request ghi single register (function 0x06)"""
        if len(frame.data) < 4:
            return {'error': 'Invalid data length'}
        
        address = struct.unpack('>H', frame.data[0:2])[0]
        value = struct.unpack('>H', frame.data[2:4])[0]
        
        return {
            'type': 'Write Single Register Request',
            'address': address,
            'value': value,
            'value_hex': f"0x{value:04X}"
        }
    
    @staticmethod
    def analyze_frame(frame: ModbusFrame) -> Dict[str, Any]:
        """Phân tích chi tiết frame dựa vào function code"""
        result = frame.to_dict()
        
        if frame.function_code == ModbusFunction.READ_HOLDING_REGISTERS.value:
            # Phân biệt request/response dựa vào độ dài data
            if len(frame.data) == 4:
                result['details'] = ModbusRTUAnalyzer.parse_read_holding_registers_request(frame)
            else:
                result['details'] = ModbusRTUAnalyzer.parse_read_holding_registers_response(frame)
        
        elif frame.function_code == ModbusFunction.WRITE_SINGLE_REGISTER.value:
            result['details'] = ModbusRTUAnalyzer.parse_write_single_register_request(frame)
        
        # Thêm các function code khác ở đây...
        
        return result


class FrameDefinition:
    """Định nghĩa custom frame structure"""
    
    def __init__(self, name: str):
        self.name = name
        self.fields: List[Dict[str, Any]] = []
        self.checksum_func: Optional[Callable] = None
    
    def add_field(self, name: str, field_type: str, size: int = 1, 
                  description: str = "", format_func: Optional[Callable] = None):
        """
        Thêm field vào frame definition
        Args:
            name: tên field
            field_type: 'uint8', 'uint16', 'uint32', 'int8', 'int16', 'int32', 'float', 'bytes', 'string'
            size: kích thước (bytes), chỉ áp dụng cho 'bytes' và 'string'
            description: mô tả field
            format_func: function để format giá trị hiển thị
        """
        self.fields.append({
            'name': name,
            'type': field_type,
            'size': size,
            'description': description,
            'format_func': format_func
        })
    
    def set_checksum_function(self, func: Callable[[bytes], int]):
        """Set hàm tính checksum"""
        self.checksum_func = func
    
    def parse(self, data: bytes) -> CustomFrame:
        """Parse data theo frame definition"""
        parsed_fields = {}
        offset = 0
        
        try:
            for field in self.fields:
                field_name = field['name']
                field_type = field['type']
                field_size = field['size']
                
                if offset >= len(data):
                    raise ValueError(f"Not enough data for field '{field_name}'")
                
                # Parse theo type
                if field_type == 'uint8':
                    value = data[offset]
                    offset += 1
                elif field_type == 'uint16':
                    value = struct.unpack('>H', data[offset:offset+2])[0]
                    offset += 2
                elif field_type == 'uint32':
                    value = struct.unpack('>I', data[offset:offset+4])[0]
                    offset += 4
                elif field_type == 'int8':
                    value = struct.unpack('b', data[offset:offset+1])[0]
                    offset += 1
                elif field_type == 'int16':
                    value = struct.unpack('>h', data[offset:offset+2])[0]
                    offset += 2
                elif field_type == 'int32':
                    value = struct.unpack('>i', data[offset:offset+4])[0]
                    offset += 4
                elif field_type == 'float':
                    value = struct.unpack('>f', data[offset:offset+4])[0]
                    offset += 4
                elif field_type == 'bytes':
                    value = data[offset:offset+field_size]
                    offset += field_size
                elif field_type == 'string':
                    value = data[offset:offset+field_size].decode('utf-8', errors='replace')
                    offset += field_size
                else:
                    raise ValueError(f"Unknown field type: {field_type}")
                
                # Format nếu có format_func
                if field['format_func']:
                    value = field['format_func'](value)
                
                parsed_fields[field_name] = value
            
            # Validate checksum nếu có
            is_valid = True
            error_msg = None
            if self.checksum_func:
                calculated_checksum = self.checksum_func(data)
                # Giả sử checksum là byte cuối
                if len(data) > 0:
                    received_checksum = data[-1]
                    is_valid = (calculated_checksum == received_checksum)
                    if not is_valid:
                        error_msg = f"Checksum mismatch: received={received_checksum:02X}, calculated={calculated_checksum:02X}"
            
            return CustomFrame(
                raw_data=data,
                parsed_fields=parsed_fields,
                is_valid=is_valid,
                error_msg=error_msg
            )
            
        except Exception as e:
            return CustomFrame(
                raw_data=data,
                parsed_fields=parsed_fields,
                is_valid=False,
                error_msg=str(e)
            )


class CustomFrameAnalyzer:
    """Analyzer cho custom frame"""
    
    def __init__(self):
        self.frame_definitions: Dict[str, FrameDefinition] = {}
    
    def add_definition(self, definition: FrameDefinition):
        """Thêm frame definition"""
        self.frame_definitions[definition.name] = definition
    
    def remove_definition(self, name: str):
        """Xóa frame definition"""
        if name in self.frame_definitions:
            del self.frame_definitions[name]
    
    def parse_frame(self, data: bytes, definition_name: str) -> Optional[CustomFrame]:
        """Parse frame theo definition"""
        if definition_name not in self.frame_definitions:
            return None
        
        definition = self.frame_definitions[definition_name]
        return definition.parse(data)
    
    def get_definition_names(self) -> List[str]:
        """Lấy danh sách tên của các definitions"""
        return list(self.frame_definitions.keys())


# Example: Tạo một frame definition mẫu
def create_sample_frame_definition() -> FrameDefinition:
    """Tạo một frame definition mẫu"""
    definition = FrameDefinition("Sample Frame")
    
    definition.add_field("header", "uint8", description="Frame header (0xAA)")
    definition.add_field("command", "uint8", description="Command byte")
    definition.add_field("data_length", "uint8", description="Data length")
    definition.add_field("data", "bytes", size=10, description="Payload data")
    definition.add_field("checksum", "uint8", description="XOR checksum")
    
    # Hàm tính checksum XOR
    def xor_checksum(data: bytes) -> int:
        checksum = 0
        for byte in data[:-1]:  # Không tính byte checksum
            checksum ^= byte
        return checksum
    
    definition.set_checksum_function(xor_checksum)
    
    return definition
