"""
Port Config Dialog
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QComboBox, QPushButton, QLabel, QGroupBox)
from PyQt6.QtCore import Qt
from ...core.serial_manager import SerialPortManager, SerialConfig
from ...utils.config_manager import ConfigManager


class PortConfigDialog(QDialog):
    """Dialog để cấu hình serial port"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config_manager = ConfigManager()
        self.serial_manager = SerialPortManager()
        
        self.setWindowTitle("Port Configuration")
        self.setModal(True)
        
        self._setup_ui()
        self._load_defaults()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Port settings group
        port_group = QGroupBox("Port Settings")
        port_layout = QFormLayout()
        
        # Port
        self.port_combo = QComboBox()
        self._refresh_ports()
        port_layout.addRow("Port:", self.port_combo)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_ports)
        port_layout.addRow("", refresh_btn)
        
        # Baudrate
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setEditable(True)
        for rate in self.serial_manager.get_baudrate_list():
            self.baudrate_combo.addItem(str(rate))
        port_layout.addRow("Baudrate:", self.baudrate_combo)
        
        # Data bits
        self.databits_combo = QComboBox()
        for bits in self.serial_manager.get_databits_list():
            self.databits_combo.addItem(str(bits))
        port_layout.addRow("Data Bits:", self.databits_combo)
        
        # Parity
        self.parity_combo = QComboBox()
        for display_name, value in self.serial_manager.get_parity_list():
            self.parity_combo.addItem(display_name, value)
        port_layout.addRow("Parity:", self.parity_combo)
        
        # Stop bits
        self.stopbits_combo = QComboBox()
        for bits in self.serial_manager.get_stopbits_list():
            self.stopbits_combo.addItem(str(bits))
        port_layout.addRow("Stop Bits:", self.stopbits_combo)
        
        # Flow Control
        self.flow_control_combo = QComboBox()
        self.flow_control_combo.addItem("None", "None")
        self.flow_control_combo.addItem("RTS/CTS (Hardware)", "RTS/CTS")
        self.flow_control_combo.addItem("XON/XOFF (Software)", "XON/XOFF")
        port_layout.addRow("Flow Control:", self.flow_control_combo)
        
        port_group.setLayout(port_layout)
        layout.addWidget(port_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Apply style
        self._apply_style()
    
    def _refresh_ports(self):
        """Refresh danh sách ports"""
        self.port_combo.clear()
        
        ports = self.serial_manager.list_available_ports()
        
        if not ports:
            self.port_combo.addItem("No ports available")
            return
        
        for port_info in ports:
            display_text = f"{port_info['port']} - {port_info['description']}"
            self.port_combo.addItem(display_text, port_info['port'])
    
    def _load_defaults(self):
        """Load default values từ config"""
        # Load last used config
        last_config = self.config_manager.get("serial.last_port_config", {})
        
        # Port - try to select last used port
        last_port = last_config.get("port", "")
        if last_port:
            for i in range(self.port_combo.count()):
                if self.port_combo.itemData(i) == last_port:
                    self.port_combo.setCurrentIndex(i)
                    break
        
        # Baudrate
        baudrate = last_config.get("baudrate", self.config_manager.get("serial.default_baudrate", 9600))
        index = self.baudrate_combo.findText(str(baudrate))
        if index >= 0:
            self.baudrate_combo.setCurrentIndex(index)
        
        # Data bits
        databits = last_config.get("databits", self.config_manager.get("serial.default_databits", 8))
        index = self.databits_combo.findText(str(databits))
        if index >= 0:
            self.databits_combo.setCurrentIndex(index)
        
        # Parity
        parity_value = last_config.get("parity", "N")
        # Convert single char to display name
        parity_map = {'N': 'None', 'E': 'Even', 'O': 'Odd', 'M': 'Mark', 'S': 'Space'}
        parity_display = parity_map.get(parity_value, 'None')
        
        for i in range(self.parity_combo.count()):
            if self.parity_combo.itemText(i) == parity_display:
                self.parity_combo.setCurrentIndex(i)
                break
        
        # Stop bits
        stopbits = last_config.get("stopbits", self.config_manager.get("serial.default_stopbits", 1))
        index = self.stopbits_combo.findText(str(stopbits))
        if index >= 0:
            self.stopbits_combo.setCurrentIndex(index)
        
        # Flow Control
        flow_control = last_config.get("flow_control", "None")
        for i in range(self.flow_control_combo.count()):
            if self.flow_control_combo.itemData(i) == flow_control:
                self.flow_control_combo.setCurrentIndex(i)
                break
    
    def accept(self):
        """Override accept để save config"""
        # Save current config
        config = self.get_config()
        self.config_manager.set("serial.last_port_config", {
            "port": config.port,
            "baudrate": config.baudrate,
            "databits": config.databits,
            "parity": config.parity,
            "stopbits": config.stopbits,
            "flow_control": config.flow_control
        })
        self.config_manager.save()
        
        super().accept()
    
    def get_config(self) -> SerialConfig:
        """Lấy config từ dialog"""
        port = self.port_combo.currentData()
        if port is None:
            port = self.port_combo.currentText()
        
        baudrate = int(self.baudrate_combo.currentText())
        databits = int(self.databits_combo.currentText())
        parity = self.parity_combo.currentData()
        stopbits = float(self.stopbits_combo.currentText())
        flow_control = self.flow_control_combo.currentData()
        
        return SerialConfig(
            port=port,
            baudrate=baudrate,
            databits=databits,
            parity=parity,
            stopbits=int(stopbits),
            flow_control=flow_control
        )
    
    def _apply_style(self):
        """Áp dụng theme style"""
        # Don't apply inline style - let main theme handle it
        pass
