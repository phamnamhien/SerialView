"""
Main Window Controller
"""
from PyQt6.QtWidgets import (QMainWindow, QMessageBox, QFileDialog, QMdiArea,
                             QMenuBar, QMenu, QToolBar, QStatusBar, QWidget, 
                             QVBoxLayout, QDockWidget)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QAction
import os

from ..core.serial_manager import SerialPortManager, SerialConfig, SerialConnection
from ..core.logger import SerialLogger, DataDirection
from ..core.protocol_analyzer import create_sample_frame_definition
from ..plugins.script_engine import ScriptEngine
from ..plugins.export_manager import ExportManager
from ..utils.config_manager import ConfigManager
from .display_windows import (
    AsciiDisplayWindow, HexDisplayWindow, BinaryDisplayWindow,
    DecimalDisplayWindow, MixedDisplayWindow, ModbusDisplayWindow,
    CustomFrameDisplayWindow
)
from .dialogs.port_config import PortConfigDialog
from .send_panel import SendPanel
from datetime import datetime


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        print("Initializing MainWindow...")
        
        try:
            # Setup UI
            print("Setting up UI...")
            self._setup_ui()
            print("UI setup complete")
            
            # Initialize managers
            print("Initializing managers...")
            self.config_manager = ConfigManager()
            print("ConfigManager OK")
            
            self.serial_manager = SerialPortManager()
            print("SerialPortManager OK")
            
            self.logger = SerialLogger()
            print("SerialLogger OK")
            
            self.script_engine = ScriptEngine()
            print("ScriptEngine OK")
            
            self.export_manager = ExportManager()
            print("ExportManager OK")
            
            # Current connection
            self.current_connection: SerialConnection = None
            self.current_port = None
            self.current_session_id = None
            
            # Display windows
            self.display_windows = {}
            
            # Setup
            print("Connecting signals...")
            self._connect_signals()
            print("Signals connected")
            
            print("Applying theme...")
            saved_theme = self.config_manager.get("ui.theme", "dark")
            self._apply_theme(saved_theme)
            print("Theme applied")
            
            print("Updating UI state...")
            self._update_ui_state()
            print("UI state updated")
            
            # Load saved geometry
            self._load_window_geometry()
            
            print("MainWindow initialization complete!")
            
        except Exception as e:
            print(f"Error in MainWindow.__init__: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _setup_ui(self):
        """Setup UI bằng code"""
        self.setWindowTitle("Serial Port Monitor")
        self.resize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # MDI Area
        self.mdiArea = QMdiArea()
        layout.addWidget(self.mdiArea)
        
        # Create Send Panel as dock widget
        self.send_panel = SendPanel()
        self.send_panel.send_data.connect(self._on_send_panel_data)
        self.send_panel.connect_clicked.connect(self._on_connect_disconnect_clicked)
        self.send_panel.set_connection_state(False)  # Initially disconnected
        
        send_dock = QDockWidget("Send Panel", self)
        send_dock.setWidget(self.send_panel)
        send_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | 
                                   Qt.DockWidgetArea.TopDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, send_dock)
        
        # Create menu bar
        self._create_menus()
        
        # Create status bar
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
    
    def _create_menus(self):
        """Tạo menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        self.actionExit = QAction("Exit", self)
        file_menu.addAction(self.actionExit)
        
        # Port Menu
        port_menu = menubar.addMenu("Port")
        self.actionConnect = QAction("Connect", self)
        self.actionDisconnect = QAction("Disconnect", self)
        self.actionPortSettings = QAction("Port Settings...", self)
        port_menu.addAction(self.actionConnect)
        port_menu.addAction(self.actionDisconnect)
        port_menu.addSeparator()
        port_menu.addAction(self.actionPortSettings)
        
        # View Menu
        view_menu = menubar.addMenu("View")
        
        # New Display submenu
        new_display_menu = view_menu.addMenu("New Display")
        self.actionDisplayASCII = QAction("ASCII", self)
        self.actionDisplayHEX = QAction("HEX", self)
        self.actionDisplayBinary = QAction("Binary", self)
        self.actionDisplayDecimal = QAction("Decimal", self)
        self.actionDisplayMixed = QAction("Mixed (HEX+ASCII)", self)
        self.actionDisplayModbus = QAction("Modbus RTU", self)
        self.actionDisplayCustomFrame = QAction("Custom Frame...", self)
        
        new_display_menu.addAction(self.actionDisplayASCII)
        new_display_menu.addAction(self.actionDisplayHEX)
        new_display_menu.addAction(self.actionDisplayBinary)
        new_display_menu.addAction(self.actionDisplayDecimal)
        new_display_menu.addAction(self.actionDisplayMixed)
        new_display_menu.addSeparator()
        new_display_menu.addAction(self.actionDisplayModbus)
        new_display_menu.addAction(self.actionDisplayCustomFrame)
        
        view_menu.addSeparator()
        self.actionCascade = QAction("Cascade", self)
        self.actionTile = QAction("Tile", self)
        view_menu.addAction(self.actionCascade)
        view_menu.addAction(self.actionTile)
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        self.actionDarkTheme = QAction("Dark Theme", self)
        self.actionDarkTheme.setCheckable(True)
        self.actionLightTheme = QAction("Light Theme", self)
        self.actionLightTheme.setCheckable(True)
        self.actionLightTheme.setChecked(True)  # Default light
        theme_menu.addAction(self.actionDarkTheme)
        theme_menu.addAction(self.actionLightTheme)
        
        # Tools Menu
        tools_menu = menubar.addMenu("Tools")
        self.actionScriptEditor = QAction("Script Editor", self)
        self.actionAutoResponse = QAction("Auto Response Rules", self)
        self.actionScheduledTasks = QAction("Scheduled Tasks", self)
        self.actionExportData = QAction("Export Data...", self)
        self.actionImportData = QAction("Import Data...", self)
        
        tools_menu.addAction(self.actionScriptEditor)
        tools_menu.addAction(self.actionAutoResponse)
        tools_menu.addAction(self.actionScheduledTasks)
        tools_menu.addSeparator()
        tools_menu.addAction(self.actionExportData)
        tools_menu.addAction(self.actionImportData)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        self.actionAbout = QAction("About", self)
        help_menu.addAction(self.actionAbout)
    
    def _connect_signals(self):
        """Kết nối các signals"""
        # Menu File
        self.actionExit.triggered.connect(self.close)
        
        # Menu Port - giữ lại để có thể dùng từ menu
        self.actionConnect.triggered.connect(self._on_connect_disconnect_clicked)
        self.actionDisconnect.triggered.connect(self._on_connect_disconnect_clicked)
        self.actionPortSettings.triggered.connect(self._on_port_settings)
        
        # Menu View - New Display
        self.actionDisplayASCII.triggered.connect(lambda: self._create_display('ASCII'))
        self.actionDisplayHEX.triggered.connect(lambda: self._create_display('HEX'))
        self.actionDisplayBinary.triggered.connect(lambda: self._create_display('Binary'))
        self.actionDisplayDecimal.triggered.connect(lambda: self._create_display('Decimal'))
        self.actionDisplayMixed.triggered.connect(lambda: self._create_display('Mixed'))
        self.actionDisplayModbus.triggered.connect(lambda: self._create_display('Modbus'))
        self.actionDisplayCustomFrame.triggered.connect(lambda: self._create_display('CustomFrame'))
        
        # Menu View - Window arrangement
        self.actionCascade.triggered.connect(self.mdiArea.cascadeSubWindows)
        self.actionTile.triggered.connect(self.mdiArea.tileSubWindows)
        
        # Menu View - Theme
        self.actionDarkTheme.triggered.connect(lambda: self._apply_theme("dark"))
        self.actionLightTheme.triggered.connect(lambda: self._apply_theme("light"))
        
        # Menu Tools
        self.actionScriptEditor.triggered.connect(self._on_script_editor)
        self.actionAutoResponse.triggered.connect(self._on_auto_response)
        self.actionScheduledTasks.triggered.connect(self._on_scheduled_tasks)
        self.actionExportData.triggered.connect(self._on_export_data)
        self.actionImportData.triggered.connect(self._on_import_data)
        
        # Menu Help
        self.actionAbout.triggered.connect(self._on_about)
    
    @pyqtSlot(bytes)
    def _on_send_panel_data(self, data: bytes):
        """Xử lý khi SendPanel muốn gửi data"""
        if self.current_connection and self.current_connection.is_connected:
            self.current_connection.send_data(data)
        else:
            QMessageBox.warning(self, "Warning", "Not connected to any port")
    
    @pyqtSlot()
    def _on_connect_disconnect_clicked(self):
        """Xử lý Connect/Disconnect toggle"""
        if self.current_connection and self.current_connection.is_connected:
            # Đang connected -> disconnect
            self._disconnect()
        else:
            # Đang disconnected -> connect
            self._connect()
    
    def _connect(self):
        """Kết nối tới serial port"""
        # Hiển thị dialog chọn port
        dialog = PortConfigDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            
            # Tạo connection
            self.current_connection = self.serial_manager.create_connection(config)
            self.current_port = config.port
            
            # Connect signals
            self.current_connection.data_received.connect(self._on_data_received)
            self.current_connection.data_sent.connect(self._on_data_sent)
            self.current_connection.error_occurred.connect(self._on_error)
            self.current_connection.connection_lost.connect(self._on_connection_lost)
            
            # Connect
            if self.current_connection.connect():
                # Start logging session
                self.current_session_id = self.logger.start_session(
                    config.port, config.baudrate, config.databits,
                    config.parity, config.stopbits
                )
                
                self.statusBar().showMessage(f"Connected to {config.port}")
                self._update_ui_state()
                
                # Hiển thị thông báo kết nối
                self._show_system_message(f"Connected to {config.port} at {config.baudrate} baud", "info")
            else:
                QMessageBox.critical(self, "Error", "Failed to connect")
    
    def _disconnect(self):
        """Ngắt kết nối"""
        if not self.current_connection:
            return
        
        # Hiển thị thông báo trước khi disconnect
        self._show_system_message(f"Disconnecting from {self.current_port}", "warning")
        
        self.current_connection.disconnect()
        
        # End logging session
        if self.current_session_id:
            self.logger.end_session(self.current_session_id)
            self.current_session_id = None
        
        self.statusBar().showMessage("Disconnected")
        self._update_ui_state()
    
    @pyqtSlot()
    def _on_port_settings(self):
        """Mở dialog port settings"""
        dialog = PortConfigDialog(self)
        dialog.exec()
    
    @pyqtSlot()
    def _on_port_settings(self):
        """Mở dialog port settings - có thể thay đổi khi đang connect"""
        dialog = PortConfigDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            
            # Nếu đang connected, reconnect với config mới
            if self.current_connection and self.current_connection.is_connected:
                reply = QMessageBox.question(
                    self, "Reconnect?",
                    "Port is currently connected. Reconnect with new settings?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Disconnect
                    self._disconnect()
                    
                    # Reconnect với config mới
                    self.current_connection = self.serial_manager.create_connection(config)
                    self.current_port = config.port
                    
                    # Connect signals
                    self.current_connection.data_received.connect(self._on_data_received)
                    self.current_connection.data_sent.connect(self._on_data_sent)
                    self.current_connection.error_occurred.connect(self._on_error)
                    self.current_connection.connection_lost.connect(self._on_connection_lost)
                    
                    # Connect
                    if self.current_connection.connect():
                        self.current_session_id = self.logger.start_session(
                            config.port, config.baudrate, config.databits,
                            config.parity, config.stopbits
                        )
                        
                        self.statusBar().showMessage(f"Reconnected to {config.port}")
                        self._update_ui_state()
                        
                        # Hiển thị thông báo trên display windows
                        self._show_system_message(f"Port reconnected with new settings: {config.baudrate} baud", "info")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to reconnect")
    
    def _create_display(self, display_type: str):
        """Tạo display window mới"""
        if not self.current_port:
            QMessageBox.warning(self, "Warning", "Please connect to a port first")
            return
        
        window = None
        
        if display_type == 'ASCII':
            window = AsciiDisplayWindow.get_instance(self.current_port, 'ASCII', self)
        elif display_type == 'HEX':
            window = HexDisplayWindow.get_instance(self.current_port, 'HEX', self)
        elif display_type == 'Binary':
            window = BinaryDisplayWindow.get_instance(self.current_port, 'Binary', self)
        elif display_type == 'Decimal':
            window = DecimalDisplayWindow.get_instance(self.current_port, 'Decimal', self)
        elif display_type == 'Mixed':
            window = MixedDisplayWindow.get_instance(self.current_port, 'Mixed (HEX+ASCII)', self)
        elif display_type == 'Modbus':
            window = ModbusDisplayWindow.get_instance(self.current_port, 'Modbus RTU', self)
        elif display_type == 'CustomFrame':
            # TODO: Cho phép user chọn frame definition
            definition = create_sample_frame_definition()
            window = CustomFrameDisplayWindow.get_instance(self.current_port, f"Custom Frame: {definition.name}", definition, self)
        
        if window is None:
            QMessageBox.information(self, "Info", 
                                   f"{display_type} display already exists for this port")
            return
        
        # Add to MDI area
        sub_window = self.mdiArea.addSubWindow(window)
        window.closed.connect(self._on_display_closed)
        window.show()
        
        # Track window
        key = (self.current_port, display_type)
        self.display_windows[key] = window
    
    @pyqtSlot(bytes, datetime)
    def _show_system_message(self, message: str, msg_type: str = "info"):
        """
        Hiển thị thông báo hệ thống trên tất cả display windows
        msg_type: 'info', 'warning', 'error'
        """
        from ..core.data_parser import TimestampFormatter
        
        timestamp = datetime.now()
        
        # Chọn màu theo loại message
        color_map = {
            'info': '#3794ff',      # Blue
            'warning': '#ffcc00',   # Yellow
            'error': '#f48771'      # Red
        }
        color = color_map.get(msg_type, '#3794ff')
        
        # Update tất cả display windows
        for key, window in list(self.display_windows.items()):
            if window.port == self.current_port:
                try:
                    if window.isVisible():
                        # Hiển thị system message với màu đặc biệt
                        if hasattr(window, 'append_text'):
                            ts_str = TimestampFormatter.format_timestamp(timestamp, "%H:%M:%S.%f")
                            formatted_msg = f"[{ts_str}] ⓘ SYSTEM: {message}"
                            window.append_text(formatted_msg, color)
                except RuntimeError:
                    del self.display_windows[key]
    
    def _on_data_received(self, data: bytes, timestamp: datetime):
        """Xử lý khi nhận được dữ liệu"""
        # Log to database
        if self.current_session_id:
            self.logger.log_data(
                self.current_port, DataDirection.RX, data,
                session_id=self.current_session_id
            )
        
        # Check auto-response rules
        if self.current_connection:
            self.script_engine.check_auto_response(data, self.current_connection)
        
        # Record nếu đang recording
        self.script_engine.record_data('RX', data, timestamp)
        
        # Update tất cả display windows
        # Tạo copy để tránh lỗi khi dict thay đổi trong loop
        windows_copy = list(self.display_windows.items())
        for key, window in windows_copy:
            if window.port == self.current_port:
                try:
                    # Kiểm tra window còn tồn tại không
                    if window and not window.isHidden():
                        window.display_data(data, timestamp, 'RX')
                except RuntimeError:
                    # Window đã bị deleted, xóa khỏi dict
                    if key in self.display_windows:
                        del self.display_windows[key]
    
    @pyqtSlot(bytes, datetime)
    def _on_data_sent(self, data: bytes, timestamp: datetime):
        """Xử lý khi gửi dữ liệu"""
        # Log to database
        if self.current_session_id:
            self.logger.log_data(
                self.current_port, DataDirection.TX, data,
                session_id=self.current_session_id
            )
        
        # Record nếu đang recording
        self.script_engine.record_data('TX', data, timestamp)
        
        # Update tất cả display windows
        # Tạo copy để tránh lỗi khi dict thay đổi trong loop
        windows_copy = list(self.display_windows.items())
        for key, window in windows_copy:
            if window.port == self.current_port:
                try:
                    # Kiểm tra window còn tồn tại không
                    if window and not window.isHidden():
                        window.display_data(data, timestamp, 'TX')
                except RuntimeError:
                    # Window đã bị deleted, xóa khỏi dict
                    if key in self.display_windows:
                        del self.display_windows[key]
    
    @pyqtSlot(str)
    def _on_error(self, error_msg: str):
        """Xử lý lỗi"""
        self.statusBar().showMessage(f"Error: {error_msg}")
        self._show_system_message(f"Error: {error_msg}", "error")
        QMessageBox.critical(self, "Error", error_msg)
    
    @pyqtSlot()
    def _on_connection_lost(self):
        """Xử lý khi mất kết nối"""
        self.statusBar().showMessage("Connection lost")
        self._show_system_message("Connection lost - port disconnected", "error")
        self._update_ui_state()
    
    @pyqtSlot(str, str)
    def _on_display_closed(self, port: str, display_mode: str):
        """Xử lý khi đóng display window"""
        key = (port, display_mode)
        if key in self.display_windows:
            del self.display_windows[key]
    
    @pyqtSlot()
    def _on_script_editor(self):
        """Mở script editor"""
        # TODO: Implement script editor dialog
        QMessageBox.information(self, "Info", "Script Editor - Coming soon")
    
    @pyqtSlot()
    def _on_auto_response(self):
        """Mở auto response manager"""
        # TODO: Implement auto response dialog
        QMessageBox.information(self, "Info", "Auto Response - Coming soon")
    
    @pyqtSlot()
    def _on_scheduled_tasks(self):
        """Mở scheduled tasks manager"""
        # TODO: Implement scheduled tasks dialog
        QMessageBox.information(self, "Info", "Scheduled Tasks - Coming soon")
    
    @pyqtSlot()
    def _on_export_data(self):
        """Export dữ liệu"""
        if not self.current_port:
            QMessageBox.warning(self, "Warning", "No active connection")
            return
        
        # Chọn file
        filepath, filter_type = QFileDialog.getSaveFileName(
            self, "Export Data", "", 
            "CSV (*.csv);;Text (*.txt);;HTML (*.html);;JSON (*.json)"
        )
        
        if not filepath:
            return
        
        # Load logs từ database
        logs = self.logger.get_logs(port=self.current_port, limit=10000)
        
        # Determine format
        if filter_type == "CSV (*.csv)":
            self.export_manager.export_to_csv(logs, filepath)
        elif filter_type == "Text (*.txt)":
            self.export_manager.export_to_txt(logs, filepath)
        elif filter_type == "HTML (*.html)":
            self.export_manager.export_to_html(logs, filepath)
        elif filter_type == "JSON (*.json)":
            self.export_manager.export_to_json(logs, filepath)
        
        QMessageBox.information(self, "Success", "Data exported successfully")
    
    @pyqtSlot()
    def _on_import_data(self):
        """Import dữ liệu"""
        # TODO: Implement import
        QMessageBox.information(self, "Info", "Import Data - Coming soon")
    
    @pyqtSlot()
    def _on_about(self):
        """Hiển thị About dialog"""
        QMessageBox.about(self, "About", 
                         "Serial Port Monitor\n\n"
                         "Version 1.0\n"
                         "Professional serial port monitoring tool")
    
    def _update_ui_state(self):
        """Cập nhật trạng thái UI"""
        is_connected = False
        if self.current_connection is not None:
            is_connected = self.current_connection.is_connected
        
        self.actionConnect.setEnabled(not is_connected)
        self.actionDisconnect.setEnabled(is_connected)
        
        # Update send panel
        port_name = self.current_port if self.current_port else ""
        self.send_panel.set_connection_state(is_connected, port_name)
    
    def _apply_theme(self, theme: str = "dark"):
        """Áp dụng theme"""
        try:
            if theme == "light":
                theme_file = "light_theme.qss"
                self.actionLightTheme.setChecked(True)
                self.actionDarkTheme.setChecked(False)
                self._set_light_palette()
            else:
                theme_file = "dark_theme.qss"
                self.actionDarkTheme.setChecked(True)
                self.actionLightTheme.setChecked(False)
                self._set_dark_palette()
            
            theme_path = os.path.join(os.path.dirname(__file__),
                                     f"../../resources/styles/{theme_file}")
            
            print(f"Loading theme: {theme_path}")
            print(f"File exists: {os.path.exists(theme_path)}")
            
            if os.path.exists(theme_path):
                with open(theme_path, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                    self.setStyleSheet(stylesheet)
                    print(f"{theme.capitalize()} theme loaded successfully")
                    
                    # Save theme preference
                    self.config_manager.set("ui.theme", theme)
                    self.config_manager.save()
            else:
                print(f"Theme file not found: {theme_path}")
        except Exception as e:
            print(f"Error loading theme: {e}")
    
    def _set_dark_palette(self):
        """Set dark color palette"""
        from PyQt6.QtGui import QPalette, QColor
        from PyQt6.QtWidgets import QApplication
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.Base, QColor(37, 37, 38))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.Text, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 48))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 122, 204))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        QApplication.instance().setPalette(palette)
    
    def _set_light_palette(self):
        """Set light color palette"""
        from PyQt6.QtGui import QPalette, QColor
        from PyQt6.QtWidgets import QApplication
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(243, 243, 243))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(248, 248, 248))
        palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        QApplication.instance().setPalette(palette)
    
    def _load_window_geometry(self):
        """Load window geometry từ config"""
        geometry = self.config_manager.get("ui.window_geometry")
        if geometry:
            # TODO: Restore geometry
            pass
    
    def _save_window_geometry(self):
        """Lưu window geometry vào config"""
        # TODO: Save geometry
        pass
    
    def closeEvent(self, event):
        """Override closeEvent"""
        # Ngắt kết nối
        if self.current_connection:
            self._disconnect()
        
        # Lưu config
        self._save_window_geometry()
        self.config_manager.save()
        
        event.accept()
