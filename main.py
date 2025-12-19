"""
Serial Port Monitor - Main Entry Point
"""
import sys
import traceback
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

print("Starting Serial Port Monitor...")
print(f"Python version: {sys.version}")

try:
    print("Importing MainWindow...")
    from src.ui.main_window import MainWindow
    print("MainWindow imported successfully")
    
    def main():
        """Main function"""
        print("Creating QApplication...")
        
        # Enable High DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Serial Port Monitor")
        app.setOrganizationName("SerialPortMonitor")
        
        print("Creating MainWindow...")
        window = MainWindow()
        
        print("Showing window...")
        window.show()
        
        print("Window should be visible now!")
        print("Starting event loop...")
        
        # Run application
        sys.exit(app.exec())

    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"Error occurred: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")
