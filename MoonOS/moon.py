
import os
import sys
import time
import json
import datetime
import calendar
import subprocess
import msvcrt
import shutil
import webbrowser
import ast
import importlib.util

# --- SYSTEM INITIALIZATION ---


def initialize_system():
    # 1. THE LOOP BREAKER: If this file exists, we already tried updating.
    lock_file = ".moon_boot_lock"
    if os.path.exists(lock_file):
        # Remove it so the next manual boot works normally
        os.remove(lock_file)
        return

        # Mapping: What to check in Python -> What to install via PIP
    libraries = {
        "asciimatics": "asciimatics",
        "cv2": "opencv-python",
        "rich": "rich",
        "bs4": "beautifulsoup4",
        "PyQt5": "PyQt5",
        "pywifi": "pywifi",
        "playwright": "playwright",
        "comtypes": "comtypes"
    }

    # We check PyQtWebEngine separately because its import path is nested
    needs_update = False

    for imp_name in libraries.keys():
        try:
            __import__(imp_name)
        except ImportError:
            needs_update = True
            break

    # Special check for WebEngine
    try:
        from PyQt5 import QtWebEngineWidgets
    except ImportError:
        needs_update = True

    if needs_update:
        print("\n" + "--- MOON-OS CORE UPDATE ---".center(80))

        # Create the lock file BEFORE rebooting to prevent the loop
        with open(lock_file, "w") as f:
            f.write("locked")

        # Install/Update everything
        pip_packages = list(libraries.values()) + ["PyQtWebEngine"]
        for pkg in pip_packages:
            print(f"[+] Syncing: {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--upgrade", "--quiet"])

        # If playwright was installed, run its install step to fetch browser binaries.
        try:
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Non-fatal: we'll still attempt to relaunch and let the user see errors.
            pass

        print("\n" + "SYSTEM READY. RELAUNCHING...".center(80))
        time.sleep(1)

        # Reboot logic: relaunch directly into kernel mode to avoid an
        # intermediate process that opens and closes immediately.
        current_script = os.path.abspath(__file__)
        # Use cmd /k so the new console remains open and shows errors for debugging.
        subprocess.Popen(f'start "MoonOS Terminal" cmd /k "{sys.executable} \"{current_script}\" --kernel"', shell=True)
        sys.exit(0)


initialize_system()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.live import Live
from rich.markdown import Markdown
from bs4 import BeautifulSoup
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
import numpy as np
import cv2
from web_engine import MoonNativeBrowser
from PyQt5.QtWidgets import QApplication
import sys
try:
    import pywifi
except Exception:
    pywifi = None

console = Console()

try:
    from filesystem import MoonFS
    from wifi import MoonWiFi

    print("CORE SYSTEMS: [ OK ]")
except ImportError as e:
    print(f"CRITICAL SYSTEM FAILURE: External module not found -> {e}")
    sys.exit(1)


def boot_sequence():
    os.system('cls' if os.name == 'nt' else 'clear')
    columns, lines = shutil.get_terminal_size()

    logo = [
        r"   ╒════════════════════════════════════════════╕   ",
        r"          __  __                         ____       ",
        r"         |  \/  | ___   ___  _ __   ___ / ___|      ",
        r"         | |\/| |/ _ \ / _ \| '_ \ / _ \\___ \      ",
        r"         | |  | | (_) | (_) | | | | (_) |___) |     ",
        r"         |_|  |_|\___/ \___/|_| |_|\___/|____/      ",
        r"                                                    ",
        r"   ╘════════════════════════════════════════════╛   ",
        r"                INITIALIZING OS...              "
    ]

    padding_top = (lines - len(logo) - 4) // 2
    print("\n" * padding_top)
    for line in logo:
        print(line.center(columns))


def check_code_integrity(filename):
    """Checks if the Python file has valid syntax and can be compiled."""
    if not os.path.exists(filename):
        return False
    try:
        with open(filename, "r", encoding="utf-8") as f:
            source = f.read()
            # This compiles the code into an AST to check for SyntaxErrors
            ast.parse(source)
        return True
    except Exception as e:
        # If there is a syntax error, it will show here
        print(f"\n[!] Integrity Error in {filename}: {e}")
        return False


def check_module_loadable(module_name):
    """Checks if a library is actually functional and reachable."""
    return importlib.util.find_spec(module_name) is not None


# The New Active Check List (No time.sleep allowed!)
checks = [
    ("Validating MoonFS Core...", lambda: check_code_integrity("filesystem.py")),
    ("Testing Web Engine Logic...", lambda: check_code_integrity("web_engine.py")),
    ("Verifying MoonDrive Integrity...", lambda: os.path.exists("MoonDrive") or (os.makedirs("MoonDrive") or True)),
    ("Testing GUI Framework (PyQt5)...", lambda: check_module_loadable("PyQt5")),
    ("Checking OS Kernel Syntax...", lambda: check_code_integrity("moon.py")),
    ("Finalizing System State...", lambda: True)
]


class MoonBrowser:
    def __init__(self, url):
        self.url = url if url.startswith("http") else "https://" + url
        self.running = True
        self.page = None
        self.input_mode = False
        self.input_text = ""
        self.nav_height = 70

    def handle_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.page:
                if y < self.nav_height:
                    if 15 < x < 55:
                        try:
                            self.page.go_back();
                            return
                        except:
                            pass
                    if 65 < x < 105:
                        try:
                            self.page.go_forward();
                            return
                        except:
                            pass
                    if 120 < x < 1100:
                        self.input_mode = True
                        self.input_text = ""
                    return

                try:
                    self.page.mouse.click(x, y - self.nav_height)
                    self.input_mode = False
                except:
                    pass

        elif event == cv2.EVENT_MOUSEWHEEL:
            if self.page:
                delta = 350 if flags > 0 else -350
                try:
                    self.page.mouse.wheel(0, -delta)
                except:
                    pass

    def open(self):
        window_name = "UltraBrowser v1.0"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            self.page = browser.new_page(viewport={'width': 1280, 'height': 720})

            try:
                self.page.goto(self.url, timeout=60000)
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.setMouseCallback(window_name, self.handle_mouse)

                while self.running:
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        break

                    screenshot = self.page.screenshot(type='jpeg', quality=85)
                    img_array = np.frombuffer(screenshot, dtype=np.uint8)
                    site_frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                    total_frame = np.zeros((720 + self.nav_height, 1280, 3), dtype=np.uint8)
                    total_frame[self.nav_height:, :] = site_frame

                    # --- MODERN NAVIGATOR UI ---
                    # UI
                    for i in range(self.nav_height):
                        color = int(30 + (i * 0.5))
                        cv2.line(total_frame, (0, i), (1280, i), (color, color, color), 1)

                    # design(buttons)
                    # back
                    cv2.circle(total_frame, (35, 35), 18, (80, 80, 80), -1)
                    cv2.putText(total_frame, "<", (28, 42), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

                    # forward
                    cv2.circle(total_frame, (85, 35), 18, (80, 80, 80), -1)
                    cv2.putText(total_frame, ">", (78, 42), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

                    # 3. Address Bar
                    bar_x1, bar_y1, bar_x2, bar_y2 = 130, 18, 1150, 52
                    # color change
                    b_color = (255, 255, 255) if not self.input_mode else (60, 200, 60)
                    cv2.rectangle(total_frame, (bar_x1, bar_y1), (bar_x2, bar_y2), b_color, -1, cv2.LINE_AA)

                    #
                    cv2.putText(total_frame, ":", (140, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 2)

                    # URL Text
                    url_to_show = self.input_text + "_" if self.input_mode else self.page.url
                    cv2.putText(total_frame, url_to_show[:95], (165, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30),
                                1, cv2.LINE_AA)

                    cv2.imshow(window_name, total_frame)

                    # --- INPUT & CONTROL ---
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27: self.running = False

                    if self.input_mode:
                        if key == 13:  # Go to URL
                            target = self.input_text if "://" in self.input_text else "https://" + self.input_text
                            try:
                                self.page.goto(target)
                            except:
                                pass
                            self.input_mode = False
                        elif key == 8:
                            self.input_text = self.input_text[:-1]
                        elif 32 <= key <= 126:
                            self.input_text += chr(key)
                    else:
                        if key == ord('l') or key == ord('L'):
                            self.input_mode = True
                            self.input_text = ""
                        elif key == ord('b') or key == ord('B'):
                            try:
                                self.page.go_back()
                            except:
                                pass
                        elif key == ord('n') or key == ord('N'):
                            try:
                                self.page.go_forward()
                            except:
                                pass
                        elif key == 13:
                            self.page.keyboard.press("Enter")
                        elif key == 8:
                            self.page.keyboard.press("Backspace")
                        elif 32 <= key <= 126:
                            self.page.keyboard.type(chr(key))

            except Exception as e:
                print(f"\n[!] Browser Engine Error: {e}")

            browser.close()
            cv2.destroyAllWindows()


# --- EDITOR ---
class MoonEditor:
    def __init__(self, full_path):
        self.path = full_path
        self.lines = [""]
        if os.path.exists(self.path) and os.path.isfile(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.lines = [l.rstrip('\n') for l in f.readlines()] or [""]
        self.x, self.y = 0, 0
        self.running = True

    def save_and_exit(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines))
            self.running = False
            return True
        except:
            return False

    def render(self):
        content = []
        for i, line in enumerate(self.lines):
            if i == self.y:
                idx = min(self.x, len(line))
                before, char, after = line[:idx], (line[idx] if idx < len(line) else " "), line[idx + 1:]
                content.append(f"[bold cyan]{i + 1:2d} |[/] {before}[reverse]{char}[/reverse]{after}")
            else:
                content.append(f"[dim]{i + 1:2d} |[/] {line}")
        return Panel("\n".join(content), title=f"Editing: {self.path}", subtitle="CTRL+W: Save and Exit | ESC: Exit")

    def run(self):
        with Live(self.render(), auto_refresh=False, screen=True) as live:
            while self.running:
                live.update(self.render(), refresh=True)
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in [b'\x00', b'\xe0']:
                        arrow = msvcrt.getch()
                        if arrow == b'H':
                            self.y = max(0, self.y - 1)
                        elif arrow == b'P':
                            self.y = min(len(self.lines) - 1, self.y + 1)
                        elif arrow == b'K':
                            self.x = max(0, self.x - 1)
                        elif arrow == b'M':
                            self.x = min(len(self.lines[self.y]), self.x + 1)
                    elif key == b'\x1b':
                        self.running = False
                    elif key in [b'\x13', b'\x17']:
                        self.save_and_exit()
                    elif key == b'\x08':
                        if self.x > 0:
                            self.lines[self.y] = self.lines[self.y][:self.x - 1] + self.lines[self.y][self.x:]
                            self.x -= 1
                        elif self.y > 0:
                            old_line = self.lines.pop(self.y);
                            self.y -= 1
                            self.x = len(self.lines[self.y]);
                            self.lines[self.y] += old_line
                    elif key == b'\r':
                        self.lines.insert(self.y + 1, self.lines[self.y][self.x:])
                        self.lines[self.y] = self.lines[self.y][:self.x]
                        self.y += 1;
                        self.x = 0
                    else:
                        try:
                            char = key.decode('utf-8')
                            if char.isprintable():
                                self.lines[self.y] = self.lines[self.y][:self.x] + char + self.lines[self.y][self.x:]
                                self.x += 1
                        except:
                            pass


pass


# --- KERNEL ---
class MoonKernel:
    def __init__(self):
        self.config_file = "config.json"
        self.load_config()
        self.fs = MoonFS("MoonDrive")
        self.wifi = MoonWiFi()
        self.boot_time = time.time()
        self.history = []

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                data = json.load(f);
                self.user = data.get("user", "admin");
                self.host = data.get("host", "moon")
        else:
            self.user, self.host = "admin", "moon";
            self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump({"user": self.user, "host": self.host}, f)

    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(Panel(f"MoonOS v1.0", border_style="bold green", expand=False))
        while True:
            try:
                path_display = f"/{self.fs.drive}/{self.fs.current_dir}".replace("\\", "/").rstrip("/")
                if path_display == f"/{self.fs.drive}": path_display += "/"
                prompt = f"[bold green]{self.user}@{self.host}[/]:[bold blue]{path_display}[/]$ "

                cmd_raw = console.input(prompt).strip().split()
                if not cmd_raw: continue

                self.history.append(" ".join(cmd_raw))
                cmd, args = cmd_raw[0].lower(), cmd_raw[1:]

                if cmd == "shutdown":
                    return "EXIT"
                elif cmd == "reboot":
                    return "REBOOT"
                elif cmd == "clear":
                    os.system('cls' if os.name == 'nt' else 'clear')
                elif cmd == "pwd":
                    console.print(path_display, style="cyan")
                elif cmd == "whoami":
                    console.print(self.user, style="cyan")
                elif cmd == "echo":
                    console.print(" ".join(args))
                elif cmd == "history":
                    for i, h in enumerate(self.history): console.print(f"[dim]{i + 1:3d}[/] {h}")
                elif cmd == "df":
                    total, used, free = shutil.disk_usage(self.fs.drive)
                    t_mb, u_mb, f_mb = total // (1024 ** 2), used // (1024 ** 2), free // (1024 ** 2)
                    console.print(
                        f"Drive: [bold]{self.fs.drive}[/]\nTotal: {t_mb} MB | Used: {u_mb} MB | Free: [green]{f_mb} MB[/]",
                        style="cyan")
                elif cmd == "cp" and len(args) >= 2:
                    try:
                        shutil.copy(self.fs.get_full_path(args[0]), self.fs.get_full_path(args[1]));
                        console.print(
                            f"Copied {args[0]} -> {args[1]}", style="green")
                    except Exception as e:
                        console.print(f"Error: {e}", style="red")
                elif cmd in ["mv", "rename"] and len(args) >= 2:
                    try:
                        os.rename(self.fs.get_full_path(args[0]), self.fs.get_full_path(args[1]));
                        console.print(
                            f"Moved {args[0]} -> {args[1]}", style="green")
                    except Exception as e:
                        console.print(f"Error: {e}", style="red")
                elif cmd == "head" and args:
                    content = self.fs.read_file(args[0])
                    if content:
                        console.print("\n".join(content.splitlines()[:10]))
                    else:
                        console.print("File empty or not found.", style="red")
                elif cmd == "tail" and args:
                    content = self.fs.read_file(args[0])
                    if content:
                        console.print("\n".join(content.splitlines()[-10:]))
                    else:
                        console.print("File empty or not found.", style="red")
                elif cmd == "ls":
                    files = self.fs.list_files()
                    t = Table(title=f"Directory: {path_display}", box=None)
                    t.add_column("Name", style="cyan");
                    t.add_column("Type", style="dim")
                    for f in files:
                        is_dir = os.path.isdir(self.fs.get_full_path(f))
                        t.add_row(f + ("/" if is_dir else ""), "DIR" if is_dir else "FILE")
                    console.print(t)
                elif cmd == "cd":
                    if args:
                        if not self.fs.change_dir(args[0]): console.print("Path not found.", style="red")
                    else:
                        self.fs.current_dir = ""
                elif cmd == "touch" and args:
                    with open(self.fs.get_full_path(args[0]), "a"):
                        os.utime(self.fs.get_full_path(args[0]), None)
                elif cmd == "grep" and len(args) >= 2:
                    pattern, filename = args[0], args[1]
                    content = self.fs.read_file(filename)
                    if content:
                        for i, line in enumerate(content.splitlines()):
                            if pattern.lower() in line.lower(): console.print(
                                f"[bold yellow]Line {i + 1}:[/] {line.strip()}")
                    else:
                        console.print("File not found.", style="red")
                elif cmd == "wc" and args:
                    content = self.fs.read_file(args[0])
                    if content: console.print(
                        f"L: {len(content.splitlines())} | W: {len(content.split())} | C: {len(content)}",
                        style="magenta")
                elif cmd == "date":
                    now = datetime.datetime.now()
                    console.print(now.strftime("%A, %B %d, %Y - %H:%M:%S"), style="yellow")
                elif cmd == "cal":
                    now = datetime.datetime.now()
                    console.print(calendar.month(now.year, now.month), style="cyan")
                elif cmd == "edit" and args:
                    MoonEditor(self.fs.get_full_path(args[0])).run()
                    os.system('cls' if os.name == 'nt' else 'clear')
                elif cmd == "cat" and args:
                    content = self.fs.read_file(args[0])
                    if content: console.print(Panel(Syntax(content, "python", line_numbers=True)))
                elif cmd == "mkdir" and args:
                    self.fs.create_directory(args[0])
                elif cmd == "rm" and args:
                    self.fs.delete_file(args[0])
                elif cmd == "search" and args:
                    results = self.fs.search_files(args[0])
                    for r in results: console.print(f"[yellow]FOUND:[/] {r}")
                elif cmd == "neofetch":
                    uptime = int(time.time() - self.boot_time)
                    info = f"[bold cyan]OS:[/] MoonOS v1.0\n[bold cyan]UPTIME:[/] {uptime}s\n[bold cyan]USER:[/] {self.user}\n[bold cyan]HOST:[/] {self.host}"
                    console.print(Panel(info, title="SYSTEM STATUS", expand=False, border_style="magenta"))
                elif cmd == "help":
                    # --- NEW HELP TABLE ---
                    h = Table(title="MoonOS Reference Guide", box=None, header_style="bold magenta")
                    h.add_column("Command", style="cyan")
                    h.add_column("Description", style="white")

                    cmds = [
                        ("ls", "List files and directories"), ("cd <dir>", "Change directory"),
                        ("pwd", "Print working directory"),
                        ("mkdir <dir>", "Create a new directory"), ("rm <name>", "Remove file or directory"),
                        ("touch <file>", "Create empty file"),
                        ("cp <src> <dst>", "Copy a file"), ("mv <old> <new>", "Move or rename a file"),
                        ("edit <file>", "Open text editor"),
                        ("cat <file>", "View file contents"), ("head <file>", "View top 10 lines"),
                        ("tail <file>", "View bottom 10 lines"),
                        ("grep <ptn> <file>", "Search for text in file"), ("wc <file>", "Word/Line/Char count"),
                        ("search <name>", "Search drive for file"),
                        ("history", "Show command history"), ("df", "Show disk space"),
                        ("date / cal", "Show current date / calendar"),
                        ("neofetch", "System information"), ("whoami", "Show current user"),
                        ("setuser <name>", "Change username"),
                        ("clear", "Clear screen"), ("reboot", "Restart OS"), ("shutdown", "Exit OS"),
                        ("wifi scan", "scans nearby signals"),
                        ("wifi connect <SSID> <password>", "connects to the signal")
                        ("web <url> [-i]", "launches a native browser window (incognito optional)"),
                        ("run <app.py>", "launches a Python app in a new window")
                    ]
                    for c, d in cmds: h.add_row(c, d)
                    console.print(h)
                elif cmd == "setuser" and args:
                    self.user = args[0];
                    self.save_config();
                    console.print(f"User -> {self.user}", style="green")
                elif cmd == "wifi":
                    if not args:
                        console.print("Usage: wifi scan | wifi connect <SSID> <password>", style="yellow")
                    elif args[0] == "scan":
                        console.print("Scanning for signals...")
                        time.sleep(1.5)
                        console.print(self.wifi.scan())
                    elif args[0] == "connect" and len(args) >= 2:
                        ssid = args[1]
                        pwd = args[2] if len(args) > 2 else ""
                        console.print(f"Connecting to {ssid}...")
                        time.sleep(2)
                        if self.wifi.connect(ssid, pwd):
                            console.print(f"Connected! Local IP assigned: {self.wifi.local_ip}", style="bold green")
                        else:
                            console.print("Connection failed: Incorrect password or SSID.", style="bold red")

                elif cmd == "ifconfig":
                    status = "[bold green]UP[/]" if self.wifi.connected_ssid else "[bold red]DOWN[/]"
                    t = Table(title="Interface: wlan0")
                    t.add_row("Status", status)
                    t.add_row("SSID", str(self.wifi.connected_ssid))
                    t.add_row("IP", self.wifi.local_ip)
                    t.add_row("MAC", self.wifi.mac_address)
                    console.print(t)
                elif cmd == "web" and args:
                    target = args[0]
                    incognito_mode = "-i" in args
                    if incognito_mode:
                        args.remove("-i")
                        target = args[0]

                    app = QApplication.instance() or QApplication(sys.argv)
                    self.browser_window = MoonNativeBrowser(target, incognito=incognito_mode)
                    self.browser_window.show()
                    app.processEvents()
                elif cmd == "run" and args:
                    app_name = args[0]
                    if not app_name.endswith(".py"):
                        app_name += ".py"

                    # 1. Get Absolute Path (Windows needs the full address)
                    app_path = os.path.abspath(os.path.join("apps", app_name))
                    python_exe = sys.executable

                    if os.path.exists(app_path):
                        print(f"[MoonOS] Attempting to boot {app_name}...")

                        # 2. The "Double Quote" Fix
                        # Windows 'start' command treats the first set of quotes as a Window Title.
                        # We use /K so the window stays open if there is an error.
                        command = f'start "{app_name}" "{python_exe}" "{app_path}"'

                        try:
                            subprocess.Popen(command, shell=True)
                        except Exception as e:
                            print(f"[Launch Error]: {e}")
                    else:
                        print(f"[Error] File not found at: {app_path}")
                else:
                    console.print(f"Unknown command: {cmd}", style="dim")
            except KeyboardInterrupt:
                print("\nUse 'shutdown' to exit.")


pass

# --- BOOTLOADER ---
if __name__ == "__main__":
    initialize_system()
    current_script = os.path.abspath(__file__)

    if "--kernel" in sys.argv:
        try:
            boot_sequence()
            kernel = MoonKernel()
            status = kernel.run()
            if status == "REBOOT":
                subprocess.Popen(f'start "MoonOS Terminal" cmd /k "{sys.executable} \"{current_script}\" --kernel"', shell=True)
                sys.exit()
        except Exception as e:
            print(f"CRITICAL SYSTEM FAILURE: {e}")
            import traceback

            traceback.print_exc()
            input("Press ENTER to close...")
    else:
        subprocess.Popen(f'start "MoonOS Terminal" cmd /k "{sys.executable} \"{current_script}\" --kernel"', shell=True)
        sys.exit()
