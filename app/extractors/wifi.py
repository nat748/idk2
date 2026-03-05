"""Extract WiFi network information from iOS backup."""
from datetime import datetime

from app.backup.backup_reader import BackupReader
from app.constants import WIFI_PLISTS


def extract_wifi_networks(reader: BackupReader) -> list[dict]:
    """
    Extract known WiFi networks from the backup.

    Returns list of dicts with: ssid, bssid, last_joined, security, auto_join, hidden
    """
    networks = []

    for wifi_info in WIFI_PLISTS:
        try:
            plist = reader.read_plist(wifi_info["domain"], wifi_info["path"])
        except (FileNotFoundError, Exception):
            continue

        # Known WiFi plist structures
        known_networks = (
            plist.get("List of known networks")
            or plist.get("KnownNetworks")
            or plist.get("Remembered networks")
            or []
        )

        if isinstance(known_networks, dict):
            # iOS 16+ uses a dict keyed by BSSID or network identifier
            for key, net_data in known_networks.items():
                if isinstance(net_data, dict):
                    network = _parse_network_entry(net_data)
                    if network:
                        networks.append(network)
        elif isinstance(known_networks, list):
            for net_data in known_networks:
                if isinstance(net_data, dict):
                    network = _parse_network_entry(net_data)
                    if network:
                        networks.append(network)

        if networks:
            break  # Found data, no need to check other paths

    # Sort by last joined date (most recent first)
    networks.sort(
        key=lambda n: n.get("last_joined_sort", datetime.min), reverse=True
    )

    return networks


def _parse_network_entry(data: dict) -> dict | None:
    """Parse a single WiFi network entry from the plist."""
    ssid = (
        data.get("SSID_STR")
        or data.get("SSIDString")
        or data.get("SSID")
    )

    if not ssid:
        # Try to decode SSID from bytes
        ssid_bytes = data.get("SSID")
        if isinstance(ssid_bytes, bytes):
            try:
                ssid = ssid_bytes.decode("utf-8")
            except UnicodeDecodeError:
                ssid = ssid_bytes.hex()
        else:
            return None

    if isinstance(ssid, bytes):
        try:
            ssid = ssid.decode("utf-8")
        except UnicodeDecodeError:
            ssid = ssid.hex()

    network = {
        "ssid": ssid,
        "bssid": data.get("BSSID", ""),
    }

    # Last joined date
    last_joined = data.get("lastJoined") or data.get("LastJoined")
    if isinstance(last_joined, datetime):
        network["last_joined"] = last_joined.strftime("%Y-%m-%d %H:%M:%S")
        network["last_joined_sort"] = last_joined
    else:
        network["last_joined"] = ""
        network["last_joined_sort"] = datetime.min

    # Security type
    security = data.get("SecurityMode") or data.get("WEP") or ""
    if isinstance(security, str):
        network["security"] = security
    elif isinstance(security, bool):
        network["security"] = "WEP" if security else "Open"
    else:
        network["security"] = str(security) if security else ""

    # Additional fields
    network["auto_join"] = data.get("AutoLogin", data.get("enabled", True))
    network["hidden"] = data.get("HIDDEN_NETWORK", False)
    network["added_by"] = data.get("addedBy", "")

    return network
