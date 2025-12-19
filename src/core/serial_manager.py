"""
Serial Manager - Quản lý kết nối serial với threading
Sử dụng QThread để non-blocking UI
"""
import serial
import serial.tools.list_ports
from typing import List, Dict, Optional, Callable
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from datetime import datetime
from enum import Enum


class SerialConfig:
    """Cấu hình serial port"""
    
    def __init__(self, port: str, baudrate: int = 9600, databits: int = 8,
                 parity: str = 'N', stopbits: int = 1, timeout: float = 0.1,
                 flow_control: str = 'None'):
        self.port = port
        self.baudrate = baudrate
        self.databits = databits
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.flow_control = flow_control  # 'None', 'RTS/CTS', 'XON/XOFF'
    
    def to_dict(self) -> Dict:
        """Chuyển sang dictionary"""
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'databits': self.databits,
            'parity': self.parity,
            'stopbits': self.stopbits,
            'timeout': self.timeout,
            'flow_control': self.flow_control
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'SerialConfig':
        """Tạo từ dictionary"""
        return SerialConfig(**data)


class SerialWorker(QThread):
    """Worker thread để đọc dữ liệu serial"""
    
    # Signals
    data_received = pyqtSignal(bytes, datetime)  # data, timestamp
    error_occurred = pyqtSignal(str)  # error message
    connection_lost = pyqtSignal()
    
    def __init__(self, config: SerialConfig):
        super().__init__()
        self.config = config
        self.serial_port: Optional[serial.Serial] = None
        self.running = False
        self._stop_requested = False
    
    def run(self):
        """Main loop đọc dữ liệu"""
        try:
            # Mở serial port
            # Map flow control
            rtscts = False
            xonxoff = False
            if self.config.flow_control == 'RTS/CTS':
                rtscts = True
            elif self.config.flow_control == 'XON/XOFF':
                xonxoff = True
            
            self.serial_port = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.databits,
                parity=self.config.parity,
                stopbits=self.config.stopbits,
                timeout=self.config.timeout,
                rtscts=rtscts,
                xonxoff=xonxoff
            )
            
            self.running = True
            
            while not self._stop_requested:
                try:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        timestamp = datetime.now()
                        self.data_received.emit(data, timestamp)
                    else:
                        # Sleep một chút để không busy wait
                        self.msleep(10)
                
                except serial.SerialException as e:
                    self.error_occurred.emit(f"Serial error: {str(e)}")
                    self.connection_lost.emit()
                    break
                except Exception as e:
                    self.error_occurred.emit(f"Unexpected error: {str(e)}")
                    break
            
        except serial.SerialException as e:
            self.error_occurred.emit(f"Failed to open port: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
        finally:
            self._cleanup()
    
    def write_data(self, data: bytes) -> bool:
        """Ghi dữ liệu ra serial port"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(data)
                return True
            return False
        except Exception as e:
            self.error_occurred.emit(f"Write error: {str(e)}")
            return False
    
    def stop(self):
        """Dừng worker thread"""
        self._stop_requested = True
    
    def _cleanup(self):
        """Cleanup khi thread kết thúc"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
        self.running = False


class SerialConnection(QObject):
    """
    Quản lý một kết nối serial
    Wrapper cho SerialWorker với signals
    """
    
    # Signals
    data_received = pyqtSignal(bytes, datetime)
    data_sent = pyqtSignal(bytes, datetime)
    error_occurred = pyqtSignal(str)
    connection_lost = pyqtSignal()
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    
    def __init__(self, config: SerialConfig):
        super().__init__()
        self.config = config
        self.worker: Optional[SerialWorker] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Kết nối tới serial port"""
        if self.is_connected:
            return True
        
        try:
            self.worker = SerialWorker(self.config)
            
            # Connect signals
            self.worker.data_received.connect(self._on_data_received)
            self.worker.error_occurred.connect(self._on_error)
            self.worker.connection_lost.connect(self._on_connection_lost)
            
            # Start worker thread
            self.worker.start()
            
            self.is_connected = True
            self.connected.emit()
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Ngắt kết nối"""
        if not self.is_connected:
            return
        
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)  # Đợi tối đa 3s
            
            if self.worker.isRunning():
                self.worker.terminate()
            
            self.worker = None
        
        self.is_connected = False
        self.disconnected.emit()
    
    def send_data(self, data: bytes) -> bool:
        """Gửi dữ liệu"""
        if not self.is_connected or not self.worker:
            return False
        
        success = self.worker.write_data(data)
        if success:
            timestamp = datetime.now()
            self.data_sent.emit(data, timestamp)
        
        return success
    
    def _on_data_received(self, data: bytes, timestamp: datetime):
        """Xử lý khi nhận được dữ liệu"""
        self.data_received.emit(data, timestamp)
    
    def _on_error(self, error_msg: str):
        """Xử lý lỗi"""
        self.error_occurred.emit(error_msg)
    
    def _on_connection_lost(self):
        """Xử lý khi mất kết nối"""
        self.is_connected = False
        self.connection_lost.emit()
        self.disconnected.emit()


class SerialPortManager:
    """
    Manager quản lý nhiều serial connections
    Singleton pattern
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.connections: Dict[str, SerialConnection] = {}
    
    @staticmethod
    def list_available_ports() -> List[Dict[str, str]]:
        """Liệt kê các cổng serial có sẵn"""
        ports = serial.tools.list_ports.comports()
        return [
            {
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid
            }
            for port in ports
        ]
    
    def create_connection(self, config: SerialConfig) -> Optional[SerialConnection]:
        """Tạo connection mới"""
        port_name = config.port
        
        # Kiểm tra nếu đã có connection
        if port_name in self.connections:
            return self.connections[port_name]
        
        # Tạo connection mới
        connection = SerialConnection(config)
        self.connections[port_name] = connection
        
        return connection
    
    def get_connection(self, port: str) -> Optional[SerialConnection]:
        """Lấy connection theo port"""
        return self.connections.get(port)
    
    def remove_connection(self, port: str):
        """Xóa connection"""
        if port in self.connections:
            connection = self.connections[port]
            if connection.is_connected:
                connection.disconnect()
            del self.connections[port]
    
    def disconnect_all(self):
        """Ngắt tất cả connections"""
        for connection in self.connections.values():
            if connection.is_connected:
                connection.disconnect()
    
    def get_all_connections(self) -> Dict[str, SerialConnection]:
        """Lấy tất cả connections"""
        return self.connections.copy()
    
    @staticmethod
    def get_baudrate_list() -> List[int]:
        """Danh sách baudrate thông dụng"""
        return [
            110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
            38400, 57600, 115200, 128000, 256000, 460800, 921600
        ]
    
    @staticmethod
    def get_databits_list() -> List[int]:
        """Danh sách databits"""
        return [5, 6, 7, 8]
    
    @staticmethod
    def get_parity_list() -> List[tuple]:
        """Danh sách parity (display_name, value)"""
        return [
            ('None', 'N'),
            ('Even', 'E'),
            ('Odd', 'O'),
            ('Mark', 'M'),
            ('Space', 'S')
        ]
    
    @staticmethod
    def get_stopbits_list() -> List[float]:
        """Danh sách stopbits"""
        return [1, 1.5, 2]
