import subprocess
import os


class MoonWiFi:
    def __init__(self):
        self.interface = "Wi-Fi"

    def scan(self):
        """Scans real nearby WiFi networks using Windows netsh."""
        try:
            output = subprocess.check_output("netsh wlan show networks", shell=True).decode('ascii', errors='ignore')
            networks = []
            for line in output.split('\n'):
                if "SSID" in line and ":" in line:
                    ssid = line.split(":")[1].strip()
                    if ssid: networks.append(ssid)
            return networks
        except:
            return []

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
            return res.returncode == 0
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