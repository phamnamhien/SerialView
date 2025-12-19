# Serial Port Monitor - Kiến Trúc Dự Án

## Cấu Trúc Thư Mục

```
SerialPortMonitor/
├── src/
│   ├── core/                      # Core libraries
│   │   ├── serial_manager.py      # Quản lý kết nối serial
│   │   ├── data_parser.py         # Parse và format dữ liệu
│   │   ├── protocol_analyzer.py   # Phân tích protocol (Modbus, custom)
│   │   └── logger.py              # Logging system
│   ├── ui/
│   │   ├── main_window.py         # Main window controller
│   │   ├── display_windows/       # Các cửa sổ hiển thị
│   │   │   ├── base_display.py    # Base class cho tất cả display
│   │   │   ├── ascii_display.py   # ASCII display
│   │   │   ├── hex_display.py     # HEX display
│   │   │   ├── modbus_display.py  # Modbus RTU display
│   │   │   └── custom_frame_display.py
│   │   └── dialogs/               # Dialog boxes
│   │       ├── port_config.py
│   │       └── script_editor.py
│   ├── plugins/
│   │   ├── script_engine.py       # Script automation engine
│   │   └── export_manager.py      # Export data (CSV, TXT, etc)
│   └── utils/
│       ├── config_manager.py      # Quản lý cấu hình
│       └── helpers.py             # Helper functions
├── resources/
│   ├── icons/                     # Icon files
│   ├── styles/                    # QSS style files
│   │   └── dark_theme.qss
│   └── ui/                        # Qt Designer .ui files
│       ├── main_window.ui
│       ├── port_config.ui
│       └── script_editor.ui
├── config/
│   ├── default_config.json        # Cấu hình mặc định
│   └── user_config.json           # Cấu hình người dùng
├── logs/                          # Log files
├── scripts/
│   └── templates/                 # Script templates
├── main.py                        # Entry point
└── requirements.txt
```

## Kiến Trúc

### 1. Core Layer
- **serial_manager.py**: Quản lý tất cả kết nối serial, sử dụng QThread để non-blocking
- **data_parser.py**: Convert giữa các format (ASCII, HEX, Binary, Decimal)
- **protocol_analyzer.py**: Phân tích protocol (Modbus RTU, custom frame)
- **logger.py**: Ghi log vào file, database SQLite

### 2. UI Layer
- **main_window.py**: MDI (Multi Document Interface) chính
- **display_windows/**: Các cửa sổ con hiển thị dữ liệu
  - BaseDisplayWindow: Abstract base class
  - Mỗi display mode kế thừa từ BaseDisplayWindow
  - Singleton pattern cho mỗi mode per port

### 3. Plugin Layer
- **script_engine.py**: Python embedded scripting
- **export_manager.py**: Export/Import data

### 4. Utils Layer
- Các utility functions dùng chung

## Design Patterns Sử dụng

1. **Singleton**: ConfigManager, ScriptEngine
2. **Observer**: Serial data events
3. **Factory**: Display window creation
4. **Strategy**: Data parsing strategies
5. **Command**: Script commands

## Threading Model

- **Main Thread**: UI
- **Serial Thread**: Mỗi port một QThread riêng
- **Script Thread**: Background execution
- **Signal/Slot**: Communication giữa threads

## Database Schema (SQLite)

```sql
-- logs table
CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    port TEXT,
    direction TEXT, -- 'TX' or 'RX'
    data BLOB,
    display_mode TEXT
);

-- scripts table
CREATE TABLE scripts (
    id INTEGER PRIMARY KEY,
    name TEXT,
    content TEXT,
    created_at DATETIME
);

-- sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    port TEXT,
    baudrate INTEGER,
    start_time DATETIME,
    end_time DATETIME
);
```

## Dependencies

- PyQt6
- pyserial
- sqlite3 (built-in)
- pymodbus (cho Modbus analyzer)
