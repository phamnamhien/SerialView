"""
Test PyQt6 simple window
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Test Window")
window.resize(400, 300)

label = QLabel("Hello World!", window)
label.move(150, 120)

window.show()

print("Window should be visible now")
sys.exit(app.exec())
