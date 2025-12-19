"""
Config Manager - Singleton pattern
Quản lý tất cả cấu hình của ứng dụng
"""
import json
import os
from typing import Any, Dict


class ConfigManager:
    """Singleton class quản lý cấu hình"""
    
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
        self.config_dir = "config"
        self.default_config_path = os.path.join(self.config_dir, "default_config.json")
        self.user_config_path = os.path.join(self.config_dir, "user_config.json")
        
        self._ensure_config_dir()
        self.config = self._load_config()
    
    def _ensure_config_dir(self):
        """Đảm bảo thư mục config tồn tại"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Cấu hình mặc định"""
        return {
            "serial": {
                "default_baudrate": 9600,
                "default_databits": 8,
                "default_parity": "None",
                "default_stopbits": 1,
                "default_timeout": 1.0,
                "last_port": "",
                "last_port_config": {
                    "port": "",
                    "baudrate": 9600,
                    "databits": 8,
                    "parity": "N",
                    "stopbits": 1,
                    "flow_control": "None"
                }
            },
            "ui": {
                "theme": "light",
                "font_family": "Consolas",
                "font_size": 10,
                "window_geometry": None,
                "mdi_mode": True
            },
            "display": {
                "timestamp_format": "%Y-%m-%d %H:%M:%S.%f",
                "max_buffer_lines": 10000,
                "auto_scroll": True,
                "show_hex_address": True
            },
            "logging": {
                "enabled": True,
                "log_dir": "logs",
                "max_log_size_mb": 100,
                "log_level": "INFO"
            },
            "script": {
                "auto_save": True,
                "templates_dir": "scripts/templates"
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load cấu hình từ file"""
        # Load default config
        default_config = self._get_default_config()
        
        # Tạo default config file nếu chưa có
        if not os.path.exists(self.default_config_path):
            self._save_json(self.default_config_path, default_config)
        
        # Load user config nếu có
        if os.path.exists(self.user_config_path):
            try:
                user_config = self._load_json(self.user_config_path)
                # Merge với default config
                return self._merge_configs(default_config, user_config)
            except Exception as e:
                print(f"Error loading user config: {e}")
                return default_config
        
        return default_config
    
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_json(self, path: str, data: Dict[str, Any]):
        """Save JSON file"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Merge user config vào default config"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Lấy giá trị config theo key path
        VD: get("serial.default_baudrate")
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set giá trị config theo key path
        VD: set("serial.default_baudrate", 115200)
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """Lưu config hiện tại vào user config file"""
        try:
            self._save_json(self.user_config_path, self.config)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def reset_to_default(self):
        """Reset về cấu hình mặc định"""
        self.config = self._get_default_config()
        if os.path.exists(self.user_config_path):
            os.remove(self.user_config_path)
