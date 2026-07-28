import os
import sys
import ast
import subprocess
import backups  # This contains your SYSTEM_PY strings


class MoonSentinel:
    def __init__(self):
        self.system_files = ["moon.py", "web_engine.py", "filesystem.py", "backups.py"]
        self.health_report = {}

    def scan_integrity(self):
        print("--- MOON-OS SENTINEL: SYSTEM SCAN ---")
        all_clear = True

        for file in self.system_files:
            status = "[OK]"
            if not os.path.exists(file):
                status = "[MISSING]"
                all_clear = False
            else:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        ast.parse(f.read())  # Check for syntax errors
                except Exception as e:
                    status = f"[CORRUPTED: {e}]"
                    all_clear = False

            self.health_report[file] = status
            print(f"{file:<15} {status}")

        return all_clear

    def recover_system(self):
        print("\n[!!!] STARTING EMERGENCY RECOVERY [!!!]")
        for file, status in self.health_report.items():
            if status != "[OK]":
                if file in backups.SYSTEM_PY:
                    print(f"Repairing {file}...")
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(backups.SYSTEM_PY[file])
                else:
                    print(f"CRITICAL: No backup found for {file}!")
        print("\nRecovery Complete. Re-validating...")


def boot_sequence():
    sentinel = MoonSentinel()
    if not sentinel.scan_integrity():
        sentinel.recover_system()
        # Re-check after recovery
        if not sentinel.scan_integrity():
            print("System is beyond auto-repair. Check backups.py.")
            sys.exit(1)

    print("\n[SUCCESS] Integrity Verified. Launching MoonOS...")
    # Launch the actual OS
    subprocess.call([sys.executable, "moon.py"])


if __name__ == "__main__":
    boot_sequence()