"""
Script Engine - Python script automation
Hỗ trợ:
- Send data theo lịch trình
- Auto-response khi nhận pattern
- Record/Replay
- Custom Python scripts
"""
from typing import Dict, Any, Optional, Callable, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime
import re
import time


class ScriptContext:
    """Context cho script execution"""
    
    def __init__(self, serial_connection, logger):
        self.serial = serial_connection
        self.logger = logger
        self.variables: Dict[str, Any] = {}
        self.last_received_data: bytes = b''
        self.last_sent_data: bytes = b''
    
    def send(self, data: bytes):
        """Gửi dữ liệu qua serial"""
        if self.serial:
            self.serial.send_data(data)
            self.last_sent_data = data
    
    def send_hex(self, hex_str: str):
        """Gửi dữ liệu dạng hex string"""
        from ..core.data_parser import DataParser
        data = DataParser.hex_string_to_bytes(hex_str)
        self.send(data)
    
    def send_string(self, text: str):
        """Gửi dữ liệu dạng string"""
        self.send(text.encode('utf-8'))
    
    def wait(self, seconds: float):
        """Đợi một khoảng thời gian"""
        time.sleep(seconds)
    
    def log(self, message: str):
        """Ghi log"""
        print(f"[Script] {message}")
    
    def set_var(self, name: str, value: Any):
        """Set biến"""
        self.variables[name] = value
    
    def get_var(self, name: str, default: Any = None) -> Any:
        """Lấy biến"""
        return self.variables.get(name, default)


class AutoResponseRule:
    """Rule cho auto-response"""
    
    def __init__(self, name: str, pattern: bytes, response: bytes, 
                 pattern_type: str = "exact", delay_ms: int = 0):
        """
        Args:
            name: tên rule
            pattern: pattern để match
            response: response để gửi
            pattern_type: 'exact', 'contains', 'regex', 'starts_with', 'ends_with'
            delay_ms: delay trước khi gửi response (milliseconds)
        """
        self.name = name
        self.pattern = pattern
        self.response = response
        self.pattern_type = pattern_type
        self.delay_ms = delay_ms
        self.enabled = True
        self.match_count = 0
    
    def matches(self, data: bytes) -> bool:
        """Kiểm tra data có match với pattern không"""
        if not self.enabled:
            return False
        
        if self.pattern_type == "exact":
            return data == self.pattern
        elif self.pattern_type == "contains":
            return self.pattern in data
        elif self.pattern_type == "starts_with":
            return data.startswith(self.pattern)
        elif self.pattern_type == "ends_with":
            return data.endswith(self.pattern)
        elif self.pattern_type == "regex":
            try:
                return re.search(self.pattern, data) is not None
            except:
                return False
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển sang dict"""
        return {
            'name': self.name,
            'pattern': self.pattern.hex(),
            'response': self.response.hex(),
            'pattern_type': self.pattern_type,
            'delay_ms': self.delay_ms,
            'enabled': self.enabled,
            'match_count': self.match_count
        }


class ScheduledTask:
    """Task được lên lịch"""
    
    def __init__(self, name: str, data: bytes, interval_ms: int, repeat: int = -1):
        """
        Args:
            name: tên task
            data: dữ liệu để gửi
            interval_ms: khoảng thời gian giữa các lần gửi (ms)
            repeat: số lần lặp (-1 = infinite)
        """
        self.name = name
        self.data = data
        self.interval_ms = interval_ms
        self.repeat = repeat
        self.enabled = True
        self.sent_count = 0
        self.timer: Optional[QTimer] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển sang dict"""
        return {
            'name': self.name,
            'data': self.data.hex(),
            'interval_ms': self.interval_ms,
            'repeat': self.repeat,
            'enabled': self.enabled,
            'sent_count': self.sent_count
        }


class RecordSession:
    """Session record dữ liệu"""
    
    def __init__(self, name: str):
        self.name = name
        self.records: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
    
    def add_record(self, direction: str, data: bytes, timestamp: datetime):
        """Thêm record"""
        if self.start_time is None:
            self.start_time = timestamp
            elapsed_ms = 0
        else:
            elapsed_ms = int((timestamp - self.start_time).total_seconds() * 1000)
        
        self.records.append({
            'direction': direction,
            'data': data,
            'elapsed_ms': elapsed_ms
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển sang dict"""
        return {
            'name': self.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'records': [
                {
                    'direction': r['direction'],
                    'data': r['data'].hex(),
                    'elapsed_ms': r['elapsed_ms']
                }
                for r in self.records
            ]
        }


class ScriptEngine(QObject):
    """
    Script Engine - Quản lý automation scripts
    """
    
    # Signals
    script_output = pyqtSignal(str)  # Output từ script
    script_error = pyqtSignal(str)   # Error từ script
    rule_matched = pyqtSignal(str)   # Auto-response rule matched
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.auto_response_rules: List[AutoResponseRule] = []
        self.scheduled_tasks: List[ScheduledTask] = []
        self.current_recording: Optional[RecordSession] = None
        self.saved_recordings: Dict[str, RecordSession] = {}
    
    def execute_script(self, script_code: str, context: ScriptContext):
        """
        Execute Python script
        Script có thể sử dụng context để tương tác với serial
        """
        try:
            # Tạo namespace cho script
            namespace = {
                'ctx': context,
                'send': context.send,
                'send_hex': context.send_hex,
                'send_string': context.send_string,
                'wait': context.wait,
                'log': context.log,
                'set_var': context.set_var,
                'get_var': context.get_var,
            }
            
            # Execute script
            exec(script_code, namespace)
            
        except Exception as e:
            error_msg = f"Script error: {str(e)}"
            self.script_error.emit(error_msg)
    
    def add_auto_response_rule(self, rule: AutoResponseRule):
        """Thêm auto-response rule"""
        self.auto_response_rules.append(rule)
    
    def remove_auto_response_rule(self, rule_name: str):
        """Xóa auto-response rule"""
        self.auto_response_rules = [r for r in self.auto_response_rules if r.name != rule_name]
    
    def check_auto_response(self, data: bytes, serial_connection) -> bool:
        """
        Kiểm tra data với auto-response rules
        Trả về True nếu có rule match
        """
        matched = False
        
        for rule in self.auto_response_rules:
            if rule.matches(data):
                matched = True
                rule.match_count += 1
                
                self.rule_matched.emit(rule.name)
                
                # Gửi response (với delay nếu cần)
                if rule.delay_ms > 0:
                    QTimer.singleShot(rule.delay_ms, 
                                     lambda: serial_connection.send_data(rule.response))
                else:
                    serial_connection.send_data(rule.response)
        
        return matched
    
    def add_scheduled_task(self, task: ScheduledTask, serial_connection):
        """Thêm scheduled task"""
        self.scheduled_tasks.append(task)
        
        # Tạo timer cho task
        task.timer = QTimer()
        task.timer.setInterval(task.interval_ms)
        
        def send_task_data():
            if not task.enabled:
                return
            
            serial_connection.send_data(task.data)
            task.sent_count += 1
            
            # Kiểm tra repeat count
            if task.repeat > 0 and task.sent_count >= task.repeat:
                task.timer.stop()
                task.enabled = False
        
        task.timer.timeout.connect(send_task_data)
        task.timer.start()
    
    def remove_scheduled_task(self, task_name: str):
        """Xóa scheduled task"""
        for task in self.scheduled_tasks:
            if task.name == task_name:
                if task.timer:
                    task.timer.stop()
                self.scheduled_tasks.remove(task)
                break
    
    def start_recording(self, name: str):
        """Bắt đầu recording session"""
        self.current_recording = RecordSession(name)
    
    def stop_recording(self):
        """Dừng recording và lưu"""
        if self.current_recording:
            self.saved_recordings[self.current_recording.name] = self.current_recording
            self.current_recording = None
    
    def record_data(self, direction: str, data: bytes, timestamp: datetime):
        """Record data nếu đang recording"""
        if self.current_recording:
            self.current_recording.add_record(direction, data, timestamp)
    
    def replay_recording(self, name: str, serial_connection, speed: float = 1.0):
        """
        Replay recording
        Args:
            name: tên recording
            serial_connection: kết nối serial
            speed: tốc độ replay (1.0 = normal, 2.0 = 2x, 0.5 = 0.5x)
        """
        if name not in self.saved_recordings:
            self.script_error.emit(f"Recording '{name}' not found")
            return
        
        recording = self.saved_recordings[name]
        
        # Replay các records theo thời gian
        for record in recording.records:
            if record['direction'] == 'TX':
                delay_ms = int(record['elapsed_ms'] / speed)
                QTimer.singleShot(delay_ms, 
                                 lambda d=record['data']: serial_connection.send_data(d))
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Lấy tất cả auto-response rules"""
        return [rule.to_dict() for rule in self.auto_response_rules]
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Lấy tất cả scheduled tasks"""
        return [task.to_dict() for task in self.scheduled_tasks]
    
    def get_all_recordings(self) -> List[str]:
        """Lấy danh sách tên recordings"""
        return list(self.saved_recordings.keys())
