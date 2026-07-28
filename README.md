# 🌙 MoonOS Core v 1.0

> [!WARNING]
> **SYSTEM COMPATIBILITY & DEPENDENCY NOTICE**
> 
> 1. **Windows Required:** MoonOS relies heavily on `msvcrt` for keyboard input, `PyQt5`, and `cmd` window management. Running on Linux or macOS without adaptation will cause terminal input errors.
> 2. **External Module Files:** MoonOS requires `filesystem.py`, `web_engine.py`, and `wifi.py` in the root folder to access full filesystem and network capabilities.
> 3. **First-Boot Auto-Update:** On first startup, MoonOS will auto-install missing packages (`rich`, `PyQt5`, `playwright`, `opencv-python`, etc.) via `pip` and restart the terminal window automatically. Do not manually interrupt this boot phase!
> 4. There is some codes thatdoesnt work fully.

---

## 🌟 Key Features

* Self-Healing Bootloader: Automatically installs missing dependencies via pip on startup and reboots cleanly.
* Core Command Kernel: Feature-rich CLI supporting standard Linux-like utilities and system inspection.
* Built-in Editor (MoonEditor): Terminal text editor with real-time key capture, line numbers, and shortcuts.
* Network Management: Built-in Wi-Fi scanner, connection manager, and network interface inspector.
* Web Integration: Launch web sessions directly using PyQt5 or system browser fallbacks.
* App Execution Sandbox: Run standalone Python applications isolated inside the apps/ directory.

---

## 📁 Project Architecture

MoonOS/
├── moon.py             # Main bootloader, kernel, and command engine
├── filesystem.py       # Virtual filesystem module (MoonFS)
├── web_engine.py       # PyQt5 GUI browser module
├── wifi.py             # Wi-Fi diagnostic & connection manager
├── config.json         # User configuration settings (auto-generated)
├── MoonDrive/          # Root directory for virtual disk storage
└── apps/               # Storage directory for executable sub-apps

---

## 🚀 Quick Start

### Requirements
- Operating System: Windows
- Language: Python 3.8 or higher installed and added to PATH

### How to Run
Open your terminal in the project root directory and execute:

    python moon.py

---

## 🛠️ Complete Command Reference

### File System Management
- ls              : List files and subdirectories in active path
- cd <dir>        : Change directory (use 'cd' alone to reset to root)
- pwd             : Print full current working directory path
- mkdir <name>    : Create a new directory
- rm <file/dir>   : Delete a file or directory
- touch <file>    : Create an empty file or update timestamp
- cp <src> <dst>  : Copy a file from source to destination
- mv <old> <new>  : Move or rename a file
- search <term>   : Recursively search MoonDrive for matching files
- df              : Display total, used, and free disk space

### File Inspection & Text Editing
- edit <file>     : Open file in MoonEditor
- cat <file>      : Display full file contents with syntax highlighting
- head <file>     : Output the first 10 lines of a file
- tail <file>     : Output the last 10 lines of a file
- grep <pat> <f>  : Search for text string patterns within a file
- wc <file>       : Count total lines, words, and characters

### Networking & Web
- wifi scan       : Scan for nearby local Wi-Fi networks
- wifi connect    : Connect to a network (wifi connect <SSID> <password>)
- ifconfig        : Display interface status, assigned IP, and MAC address
- web <url>       : Launch browser to target address (web <url> -i for incognito)

### App Execution & System Utilities
- run <app>       : Execute a Python script located in apps/ or active directory
- neofetch        : Display system status, username, host, and uptime
- whoami          : Output active user name
- setuser <name>  : Change system username and update config.json
- history         : Output list of previously executed commands
- date            : Display current day, date, and timestamp
- cal             : Output a full calendar view of the current month
- echo <text>     : Print text output to the terminal screen
- clear           : Clear terminal screen output
- reboot          : Restart the MoonOS environment
- shutdown        : Terminate and exit MoonOS

---

## ⌨️ MoonEditor Controls

When editing files using 'edit <filename>':

- Arrow Keys : Navigate cursor (Up, Down, Left, Right)
- Enter      : Create a new line
- Backspace  : Delete character behind cursor / join lines
- CTRL+W / S : Save changes and exit back to kernel shell
- ESC        : Cancel changes and exit editor

---

## 🔧 Boot & Crash Recovery Mechanism

1. Loop Prevention: Uses '.moon_boot_lock' file to prevent infinite restart loops during dependency syncing.
2. AST Syntax Checking: Compiles Python files into an Abstract Syntax Tree before execution to verify file integrity.
3. Module Fallbacks: Includes embedded fallback classes for MoonFS and MoonWiFi so kernel boot succeeds even if external modules fail to load.