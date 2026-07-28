import subprocess
import os
import re
import time


def _decode_netsh_output(output_bytes):
    try:
        return output_bytes.decode('cp866', errors='ignore')
    except Exception:
        return output_bytes.decode('utf-8', errors='ignore')


class MoonWiFi:
    def __init__(self):
        self.interface = "Wi-Fi"
        self.connected_ssid = None
        self.local_ip = None
        self.mac_address = None
        self._refresh_status()

    def _get_interfaces(self):
        try:
            output = subprocess.check_output(
                'netsh wlan show interfaces',
                shell=True,
                stderr=subprocess.STDOUT
            )
            output = _decode_netsh_output(output)
        except Exception:
            return [self.interface]

        interfaces = []
        for line in output.splitlines():
            if ":" in line:
                name, value = line.split(":", 1)
                if name.strip().lower() == "name":
                    interface_name = value.strip()
                    if interface_name:
                        interfaces.append(interface_name)
        return interfaces if interfaces else [self.interface]

    def _get_ip_address(self, interface_name):
        try:
            cmd = f'netsh interface ipv4 show addresses name="{interface_name}"'
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            output = _decode_netsh_output(output)
        except Exception:
            return None

        for line in output.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                if key in ("ip address", "ipv4 address", "ipaddress", "ip"):
                    return value.strip().split("(")[0].strip()
        return None

    def _refresh_status(self):
        interfaces = self._get_interfaces()
        if interfaces:
            self.interface = interfaces[0]
        stats = self.get_status()
        self.connected_ssid = stats.get("SSID") or stats.get("ssid")
        self.mac_address = stats.get("Physical Address") or stats.get("MAC Address") or stats.get("Physical address")
        self.local_ip = self._get_ip_address(self.interface) if self.interface else None

    def scan(self):
        """Scans real nearby WiFi networks using Windows netsh."""
        interfaces = self._get_interfaces()
        commands = []
        for if_name in interfaces:
            commands.append(f'netsh wlan show networks interface="{if_name}" mode=bssid')
            commands.append(f'netsh wlan show networks interface="{if_name}"')

        commands.append('netsh wlan show networks mode=bssid')
        commands.append('netsh wlan show networks')

        networks = []
        for cmd in commands:
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                output = output.decode('ascii', errors='ignore')
            except Exception:
                continue

            for line in output.splitlines():
                match = re.match(r"^\s*SSID\s+\d+\s*:\s*(.+)$", line, re.IGNORECASE)
                if match:
                    ssid = match.group(1).strip()
                    if ssid and ssid not in networks:
                        networks.append(ssid)

            # Fallback for unexpected output formats or localized Windows installs.
            for line in output.splitlines():
                if ":" in line:
                    parts = line.split(":", 1)
                    if "ssid" in parts[0].strip().lower():
                        ssid = parts[1].strip()
                        if ssid and ssid not in networks:
                            networks.append(ssid)

        return networks

    def connect(self, ssid, password):
        """Creates a Windows WiFi profile and attempts a real hardware connection."""
        profile_xml = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM><security><authEncryption><authentication>WPA2PSK</authentication>
    <encryption>AES</encryption><useOneX>false</useOneX></authEncryption>
    <sharedKey><keyType>passphrase</keyType><protected>false</protected>
    <keyMaterial>{password}</keyMaterial></sharedKey></security></MSM>
</WLANProfile>"""

        tmp = "temp_wifi.xml"
        with open(tmp, "w") as f:
            f.write(profile_xml)
        try:
            subprocess.run(f'netsh wlan add profile filename="{tmp}"', shell=True, capture_output=True)
            res = subprocess.run(f'netsh wlan connect name="{ssid}"', shell=True, capture_output=True)
            os.remove(tmp)
            success = res.returncode == 0
            if success:
                time.sleep(1)
                self._refresh_status()
            return success
        except:
            if os.path.exists(tmp): os.remove(tmp)
            return False

    def get_status(self):
        """Pulls live stats from the actual wireless card."""
        try:
            output = subprocess.check_output("netsh wlan show interface", shell=True).decode('ascii', errors='ignore')
            stats = {}
            for line in output.split('\n'):
                if ":" in line:
                    p = line.split(":", 1)
                    stats[p[0].strip()] = p[1].strip()
            return stats
        except:
            return {}