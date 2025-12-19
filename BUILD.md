# Build Instructions for SerialView

## Method 1: PyInstaller (Simple EXE)

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build using script
```bash
python build.py
```

### Step 3: Or build manually
```bash
pyinstaller SerialView.spec
```

Output: `dist/SerialView.exe` (single executable file)

---

## Method 2: Inno Setup (Windows Installer)

### Step 1: Build EXE first
```bash
python build.py
```

### Step 2: Install Inno Setup
Download from: https://jrsoftware.org/isdl.php

### Step 3: Compile installer
1. Open `installer.iss` in Inno Setup
2. Click "Build" -> "Compile"

Output: `installer/SerialView-Setup-1.0.exe`

---

## Method 3: cx_Freeze (Alternative)

### Install cx_Freeze
```bash
pip install cx_Freeze
```

### Create setup.py
```python
from cx_Freeze import setup, Executable

setup(
    name="SerialView",
    version="1.0",
    description="Serial port monitoring tool",
    executables=[Executable("main.py", base="Win32GUI", target_name="SerialView.exe")],
    options={
        "build_exe": {
            "packages": ["PyQt6", "serial"],
            "include_files": ["resources/", "config/"],
        }
    },
)
```

### Build
```bash
python setup.py build
```

---

## Distribution Files

After building, include:
- SerialView.exe (or installer)
- README.md
- LICENSE
- resources/ folder (if not embedded)

---

## Troubleshooting

### "Failed to execute script"
- Make sure all dependencies in requirements.txt are installed
- Check hidden imports in .spec file

### Missing resources
- Use `--add-data` to include folders
- Verify paths in .spec file

### Large file size
- Use `--onefile` for single file (slower startup)
- Use `--onedir` for folder distribution (faster startup)

### Icon not showing
- Create app.ico file in resources/icons/
- Or remove icon line from .spec file
