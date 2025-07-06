import sys
import re
from typing import Optional, List, Tuple, Dict

# Register NetAlertX directories
INSTALL_PATH = "/app"
sys.path.extend([f"{INSTALL_PATH}/server"])

import conf
from const import *
from logger import mylog
from helper import timeNowTZ, get_setting_value

#-------------------------------------------------------------------------------
# Base64 encoded HTML strings for FontAwesome icons, now with an extended icons dictionary for broader device coverage
ICONS = {
    "globe": "PGkgY2xhc3M9ImZhcyBmYS1nbG9iZSI+PC9pPg==",  # Internet or global network
    "phone": "PGkgY2xhc3M9ImZhcyBmYS1tb2JpbGUtYWx0Ij48L2k+",  # Smartphone
    "laptop": "PGkgY2xhc3M9ImZhIGZhLWxhcHRvcCI+PC9pPg==",  # Laptop
    "printer": "PGkgY2xhc3M9ImZhIGZhLXByaW50ZXIiPjwvaT4=",  # Printer
    "router": "PGkgY2xhc3M9ImZhcyBmYS1yYW5kb20iPjwvaT4=",  # Router or network switch
    "tv": "PGkgY2xhc3M9ImZhIGZhLXR2Ij48L2k+",  # Television
    "desktop": "PGkgY2xhc3M9ImZhIGZhLWRlc2t0b3AiPjwvaT4=",  # Desktop PC
    "tablet": "PGkgY2xhc3M9ImZhIGZhLXRhYmxldCI+PC9pPg==",  # Tablet
    "watch": "PGkgY2xhc3M9ImZhcyBmYS1jbG9jayI+PC9pPg==",  # Fallback to clock since smartwatch is nonfree in FontAwesome
    "camera": "PGkgY2xhc3M9ImZhIGZhLWNhbWVyYSI+PC9pPg==",  # Camera or webcam
    "home": "PGkgY2xhc3M9ImZhIGZhLWhvbWUiPjwvaT4=",  # Smart home device
    "apple": "PGkgY2xhc3M9ImZhYiBmYS1hcHBsZSI+PC9pPg==",  # Apple device
    "ethernet": "PGkgY2xhc3M9ImZhcyBmYS1uZXR3b3JrLXdpcmVkIj48L2k+",  # Free alternative for ethernet icon in FontAwesome
    "google": "PGkgY2xhc3M9ImZhYiBmYS1nb29nbGUiPjwvaT4=",  # Google device
    "raspberry": "PGkgY2xhc3M9ImZhYiBmYS1yYXNwYmVycnktcGkiPjwvaT4=",  # Raspberry Pi
    "microchip": "PGkgY2xhc3M9ImZhcyBmYS1taWNyb2NoaXAiPjwvaT4=",  # IoT or embedded device
    "server": "PGkgY2xhc3M9ImZhcyBmYS1zZXJ2ZXIiPjwvaT4=",  # Server
    "gamepad": "PGkgY2xhc3M9ImZhcyBmYS1nYW1lcGFkIj48L2k+",  # Gaming console
    "lightbulb": "PGkgY2xhc3M9ImZhcyBmYS1saWdodGJ1bGIiPjwvaT4=",  # Smart light
    "speaker": "PGkgY2xhc3M9ImZhcyBmYS12b2x1bWUtdXAiPjwvaT4=",  # Free speaker alt icon for smart speakers in FontAwesome
    "lock": "PGkgY2xhc3M9ImZhcyBmYS1sb2NrIj48L2k+",  # Security device
}

# Extended device types for comprehensive classification
DEVICE_TYPES = {
    "Internet": "Internet Gateway",
    "Phone": "Smartphone",
    "Laptop": "Laptop",
    "Printer": "Printer",
    "Router": "Router",
    "TV": "Television",
    "Desktop": "Desktop PC",
    "Tablet": "Tablet",
    "Smartwatch": "Smartwatch",
    "Camera": "Camera",
    "SmartHome": "Smart Home Device",
    "Server": "Server",
    "GamingConsole": "Gaming Console",
    "IoT": "IoT Device",
    "NetworkSwitch": "Network Switch",
    "AccessPoint": "Access Point",
    "SmartLight": "Smart Light",
    "SmartSpeaker": "Smart Speaker",
    "SecurityDevice": "Security Device",
    "Unknown": "Unknown Device",
}



#-------------------------------------------------------------------------------
# Guess device attributes such as type of device and associated device icon
def guess_device_attributes(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default_icon: str,
    default_type: str
    ) -> Tuple[str, str]:
    """
    Guess the appropriate FontAwesome icon and device type based on device attributes.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default_icon: Default icon to return if no match is found.
        default_type: Default type to return if no match is found.

    Returns:
        Tuple[str, str]: A tuple containing the guessed icon (Base64-encoded HTML string)
                         and the guessed device type (string).
    """
    mylog('debug', f"[guess_device_attributes] Guessing attributes for (vendor|mac|ip|name): ('{vendor}'|'{mac}'|'{ip}'|'{name}')")
    # Normalize inputs
    vendor = str(vendor).lower().strip() if vendor else "unknown"
    mac = str(mac).upper().strip() if mac else "00:00:00:00:00:00"
    ip = str(ip).strip() if ip else "169.254.0.0"  # APIPA address for unknown IPs per RFC 3927
    name = str(name).lower().strip() if name else "(unknown)"

    # --- Icon Guessing Logic ---
    if mac == "INTERNET":
        icon = ICONS.get("globe", default_icon)
    else:
        # Vendor-based icon guessing
        icon_vendor_patterns = {
            "apple": "apple",
            "samsung|motorola|xiaomi|huawei": "phone",
            "dell|lenovo|asus|acer": "laptop",
            "hp|epson|canon|brother": "printer",
            "cisco|ubiquiti|netgear|tp-link|d-link|mikrotik": "router",
            "lg|samsung electronics|sony|vizio": "tv",
            "raspberry pi": "raspberry",
            "google": "google",
            "espressif|particle": "microchip",
            "intel|amd": "desktop",
            "amazon": "speaker",
            "philips hue|lifx": "lightbulb",
            "aruba|meraki": "ethernet",
            "qnap|synology": "server",
            "nintendo|sony interactive|microsoft": "gamepad",
            "ring|blink|arlo": "camera",
            "nest": "home",
        }
        for pattern, icon_key in icon_vendor_patterns.items():
            if re.search(pattern, vendor, re.IGNORECASE):
                icon = ICONS.get(icon_key, default_icon)
                break
        else:
            # MAC-based icon guessing
            mac_clean = mac.replace(':', '').replace('-', '').upper()
            icon_mac_patterns = {
                "001A79|B0BE83|BC926B": "apple",
                "001B63|BC4C4C": "tablet",
                "74ACB9|002468": "ethernet",
                "B827EB": "raspberry",
                "001422|001874": "desktop",
                "001CBF|002186": "server",
            }
            for pattern_str, icon_key in icon_mac_patterns.items():
                patterns = [p.replace(':', '').replace('-', '').upper() for p in pattern_str.split('|')]
                if any(mac_clean.startswith(p) for p in patterns):
                    icon = ICONS.get(icon_key, default_icon)
                    break
            else:
                # Name-based icon guessing
                icon_name_patterns = {
                    "iphone|ipad|macbook|imac": "apple",
                    "pixel|galaxy|redmi": "phone",
                    "laptop|notebook": "laptop",
                    "printer|print": "printer",
                    "router|gateway|ap|access[ -]?point": "router",
                    "tv|television|smarttv": "tv",
                    "desktop|pc|computer": "desktop",
                    "tablet|pad": "tablet",
                    "watch|wear": "watch",
                    "camera|cam|webcam": "camera",
                    "echo|alexa|dot": "speaker",
                    "hue|lifx|bulb": "lightbulb",
                    "server|nas": "server",
                    "playstation|xbox|switch": "gamepad",
                    "raspberry|pi": "raspberry",
                    "google|chromecast|nest": "google",
                    "doorbell|lock|security": "lock",
                }
                for pattern, icon_key in icon_name_patterns.items():
                    if re.search(pattern, name, re.IGNORECASE):
                        icon = ICONS.get(icon_key, default_icon)
                        break
                else:
                    # IP-based icon guessing
                    icon_ip_patterns = {
                        r"^192\.168\.[0-1]\.1$": "router",
                        r"^10\.0\.0\.1$": "router",
                        r"^192\.168\.[0-1]\.[2-9]$": "desktop",
                        r"^192\.168\.[0-1]\.1\d{2}$": "phone",
                    }
                    for pattern, icon_key in icon_ip_patterns.items():
                        if re.match(pattern, ip):
                            icon = ICONS.get(icon_key, default_icon)
                            break
                    else:
                        icon = default_icon

    # --- Type Guessing Logic ---
    if mac == "INTERNET":
        type_ = DEVICE_TYPES.get("Internet", default_type)
    else:
        # Vendor-based type guessing
        type_vendor_patterns = {
            "apple|samsung|motorola|xiaomi|huawei": "Phone",
            "dell|lenovo|asus|acer|hp": "Laptop",
            "epson|canon|brother": "Printer",
            "cisco|ubiquiti|netgear|tp-link|d-link|mikrotik|aruba|meraki": "Router",
            "lg|samsung electronics|sony|vizio": "TV",
            "raspberry pi": "IoT",
            "google|nest": "SmartHome",
            "espressif|particle": "IoT",
            "intel|amd": "Desktop",
            "amazon": "SmartSpeaker",
            "philips hue|lifx": "SmartLight",
            "qnap|synology": "Server",
            "nintendo|sony interactive|microsoft": "GamingConsole",
            "ring|blink|arlo": "Camera",
        }
        for pattern, type_key in type_vendor_patterns.items():
            if re.search(pattern, vendor, re.IGNORECASE):
                type_ = DEVICE_TYPES.get(type_key, default_type)
                break
        else:
            # MAC-based type guessing
            mac_clean = mac.replace(':', '').replace('-', '').upper()
            type_mac_patterns = {
                "00:1A:79|B0:BE:83|BC:92:6B": "Phone",
                "00:1B:63|BC:4C:4C": "Tablet",
                "74:AC:B9|00:24:68": "AccessPoint",
                "B8:27:EB": "IoT",
                "00:14:22|00:18:74": "Desktop",
                "00:1C:BF|00:21:86": "Server",
            }
            for pattern_str, type_key in type_mac_patterns.items():
                patterns = [p.replace(':', '').replace('-', '').upper() for p in pattern_str.split('|')]
                if any(mac_clean.startswith(p) for p in patterns):
                    type_ = DEVICE_TYPES.get(type_key, default_type)
                    break
            else:
                # Name-based type guessing
                type_name_patterns = {
                    "iphone|ipad": "Phone",
                    "macbook|imac": "Laptop",
                    "pixel|galaxy|redmi": "Phone",
                    "laptop|notebook": "Laptop",
                    "printer|print": "Printer",
                    "router|gateway|ap|access[ -]?point": "Router",
                    "tv|television|smarttv": "TV",
                    "desktop|pc|computer": "Desktop",
                    "tablet|pad": "Tablet",
                    "watch|wear": "Smartwatch",
                    "camera|cam|webcam": "Camera",
                    "echo|alexa|dot": "SmartSpeaker",
                    "hue|lifx|bulb": "SmartLight",
                    "server|nas": "Server",
                    "playstation|xbox|switch": "GamingConsole",
                    "raspberry|pi": "IoT",
                    "google|chromecast|nest": "SmartHome",
                    "doorbell|lock|security": "SecurityDevice",
                }
                for pattern, type_key in type_name_patterns.items():
                    if re.search(pattern, name, re.IGNORECASE):
                        type_ = DEVICE_TYPES.get(type_key, default_type)
                        break
                else:
                    # IP-based type guessing
                    type_ip_patterns = {
                        r"^192\.168\.[0-1]\.1$": "Router",
                        r"^10\.0\.0\.1$": "Router",
                        r"^192\.168\.[0-1]\.[2-9]$": "Desktop",
                        r"^192\.168\.[0-1]\.1\d{2}$": "Phone",
                    }
                    for pattern, type_key in type_ip_patterns.items():
                        if re.match(pattern, ip):
                            type_ = DEVICE_TYPES.get(type_key, default_type)
                            break
                    else:
                        type_ = default_type

    return icon, type_

# Deprecated functions with redirects (To be removed once all calls for these have been adjusted to use the updated function)
def guess_icon(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default: str
    ) -> str:
    """
    [DEPRECATED] Guess the appropriate FontAwesome icon for a device based on its attributes.
    Use guess_device_attributes instead.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default: Default icon to return if no match is found.

    Returns:
        str: Base64-encoded FontAwesome icon HTML string.
    """
    
    icon, _ = guess_device_attributes(vendor, mac, ip, name, default, "unknown_type")
    return icon

def guess_type(
    vendor: Optional[str],
    mac: Optional[str],
    ip: Optional[str],
    name: Optional[str],
    default: str
    ) -> str:
    """
    [DEPRECATED] Guess the device type based on its attributes.
    Use guess_device_attributes instead.

    Args:
        vendor: Device vendor name.
        mac: Device MAC address.
        ip: Device IP address.
        name: Device name.
        default: Default type to return if no match is found.

    Returns:
        str: Device type from DEVICE_TYPES dictionary.
    """
    
    _, type_ = guess_device_attributes(vendor, mac, ip, name, "unknown_icon", default)
    return type_

# Handler for when this is run as a program instead of called as a module.
if __name__ == "__main__":
    mylog('error', "This module is not intended to be run directly.")
    