# SerialView

A professional serial port monitoring and debugging tool built with PyQt6.

## Features

### Core Functionality
- **Multiple Display Formats**: ASCII, HEX, Binary, Decimal, Mixed (HEX+ASCII)
- **Protocol Analysis**: Built-in Modbus RTU analyzer, custom frame definitions
- **MDI Interface**: Multiple display windows simultaneously
- **Real-time Monitoring**: Non-blocking serial communication with QThread
- **Data Logging**: SQLite database for session management and data persistence

### Advanced Features
- **Script Engine**: Python automation scripts for testing and automation
- **Auto-response Rules**: Pattern-based automatic responses
- **Scheduled Tasks**: Periodic data transmission
- **Record/Replay**: Capture and replay communication sessions
- **Export/Import**: CSV, TXT, HTML, JSON formats
- **Theme Support**: Dark and Light themes

## Installation

### Requirements
- Python 3.8+
- PyQt6 >= 6.6.0
- pyserial >= 3.5
- pymodbus >= 3.5.0

### Setup
```bash
# Clone repository
git clone <repository-url>
cd SerialView

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## Quick Start

1. **Connect to Serial Port**
   - Click "Connect" button or Port → Connect
   - Select port and configure settings (baudrate, data bits, etc.)
   - Click OK to establish connection

2. **Open Display Windows**
   - View → New Display → Select format (ASCII, HEX, etc.)
   - Multiple displays can be opened simultaneously
   - Each display shows real-time TX/RX data

3. **Send Data**
   - Use Send Panel at bottom
   - Select format: ASCII, HEX, Decimal, or Binary
   - Choose line ending: None, \n, \r, or \r\n
   - Click "Send" or enable periodic sending

## Display Modes

### Basic Formats
- **ASCII**: Human-readable text display
- **HEX**: Hexadecimal byte display
- **Binary**: Binary representation (8 bits per byte)
- **Decimal**: Decimal byte values (0-255)
- **Mixed**: Combined HEX + ASCII (hex editor style)

### Protocol Analyzers
- **Modbus RTU**: Automatic frame parsing with CRC validation
  - Shows slave ID, function code, data, and detailed analysis
  - Validates frame integrity
  - Parses common function codes (Read/Write registers, coils)

- **Custom Frame**: User-defined frame structures
  - Define custom field types (uint8, uint16, float, string, etc.)
  - Custom checksum functions
  - Field-by-field parsing and display

## Scripting

### Python Automation Scripts

Create automated test sequences using embedded Python:

```python
# Send HEX command
ctx.send_hex("01 03 00 00 00 0A C5 CD")

# Wait for response
ctx.wait(0.1)

# Send ASCII text
ctx.send_string("AT\r\n")

# Loop example
for i in range(10):
    ctx.send_hex(f"AA {i:02X} BB")
    ctx.wait(0.5)

# Variable storage
counter = ctx.get_var("counter", 0)
counter += 1
ctx.set_var("counter", counter)
```

### Auto-response Rules

Set up automatic responses to incoming patterns:
- Pattern types: exact, contains, starts_with, ends_with, regex
- Configurable delay before response
- Match counting and statistics

### Scheduled Tasks

Configure periodic data transmission:
- Set interval in milliseconds
- Optional repeat count (or infinite)
- Enable/disable on the fly

## Data Export

Export logged data in multiple formats:
- **CSV**: Timestamp, direction, hex data, ASCII data
- **TXT**: Formatted text with timestamps
- **HTML**: Styled output with syntax highlighting
- **JSON**: Structured data for processing

## Configuration

Settings stored in `config/user_config.json`:

```json
{
    "serial": {
        "default_baudrate": 115200,
        "default_databits": 8,
        "default_parity": "None",
        "default_stopbits": 1
    },
    "ui": {
        "theme": "light",
        "font_family": "Consolas",
        "font_size": 10
    },
    "display": {
        "max_buffer_lines": 10000,
        "auto_scroll": true
    }
}
```

## Architecture

```
SerialView/
├── src/
│   ├── core/              # Core functionality
│   │   ├── serial_manager.py     # Serial port management
│   │   ├── data_parser.py        # Data format conversion
│   │   ├── protocol_analyzer.py  # Protocol parsers
│   │   └── logger.py             # SQLite logging
│   ├── ui/
│   │   ├── main_window.py        # Main window
│   │   ├── display_windows/      # Display implementations
│   │   ├── dialogs/              # Configuration dialogs
│   │   └── send_panel.py         # Send control panel
│   ├── plugins/
│   │   ├── script_engine.py      # Python scripting
│   │   └── export_manager.py     # Data export
│   └── utils/
│       ├── config_manager.py     # Configuration
│       └── helpers.py            # Utilities
├── resources/
│   ├── styles/           # QSS themes
│   └── icons/            # Application icons
├── config/               # Configuration files
├── logs/                 # SQLite database
└── scripts/              # Script templates
```

## Database Schema

SQLite database tracks all communication:

**logs**: Stores all TX/RX data with timestamps
**sessions**: Tracks connection sessions with settings
**scripts**: Saves user scripts

## Keyboard Shortcuts

- **Ctrl+Q**: Exit application
- **Ctrl+O**: Connect to port
- **Ctrl+D**: Disconnect
- **Ctrl+S**: Send data
- **Ctrl+E**: Export data

## Troubleshooting

### Port Access Issues
- **Linux**: Add user to dialout group: `sudo usermod -a -G dialout $USER`
- **Windows**: Check Device Manager for COM port conflicts

### Display Not Updating
- Check "Auto Scroll" is enabled
- Verify connection status in Send Panel
- Check "Pause" button is not active

### Theme Not Loading
- Verify QSS files exist in `resources/styles/`
- Check file permissions
- Reset to default: View → Theme → Light Theme

## Development

### Adding New Display Format

1. Create new class inheriting from `TextBasedDisplayWindow` or `BaseDisplayWindow`
2. Implement `display_data()` method
3. Register in `main_window.py`

### Adding Protocol Analyzer

1. Create analyzer class in `protocol_analyzer.py`
2. Define frame structure using dataclasses
3. Implement parsing logic
4. Create display window in `display_windows/`

## License

CC0 1.0 Universal - See LICENSE file

## Author

**Pham Nam Hien**  
Email: phamnamhien@gmail.com

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs/features.

## Roadmap

- [ ] Plugin system for custom protocols
- [ ] Serial port simulator for testing
- [ ] Chart/graph visualization
- [ ] UART signal analyzer
- [ ] Batch testing framework
- [ ] Cloud logging integration