# Build Script for SerialView
# Creates standalone Windows executable

# Install PyInstaller first:
# pip install pyinstaller

# Run this script:
# python build.py

import os
import shutil
import PyInstaller.__main__

# Clean previous builds
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

# PyInstaller options
PyInstaller.__main__.run([
    'main.py',
    '--name=SerialView',
    '--onedir',  # Folder with dependencies (fixes DLL issues)
    '--windowed',  # No console window
    '--add-data=resources;resources',  # Include resources folder
    '--add-data=config;config',  # Include config folder
    '--hidden-import=serial.tools.list_ports',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--clean',
])

print("\nBuild complete! Check 'dist/SerialView' folder")
print("Run: dist\\SerialView\\SerialView.exe")