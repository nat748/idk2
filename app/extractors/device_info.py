"""Extract device information from iOS backup root plists."""
import os
from datetime import datetime

from app.constants import PRODUCT_TYPE_MAP
from app.utils.plist_utils import load_plist_file


def extract_device_info(backup_path: str) -> dict:
    """
    Extract all available device metadata from backup root-level plists.
    Returns a dict with keys like device_name, product_type, product_version, etc.
    """
    info = {}

    # Check both root and Snapshot/ locations
    bases = [backup_path, os.path.join(backup_path, "Snapshot")]

    # --- Info.plist ---
    for base in bases:
        info_plist = os.path.join(base, "Info.plist")
        if not os.path.isfile(info_plist):
            continue
        try:
            data = load_plist_file(info_plist)
            info["device_name"] = data.get(
                "Device Name", data.get("Display Name", "Unknown")
            )
            info["product_type"] = data.get("Product Type", "")
            info["product_version"] = data.get("Product Version", "")
            info["build_version"] = data.get("Build Version", "")
            info["serial_number"] = data.get("Serial Number", "")
            info["imei"] = data.get("IMEI", "")
            info["meid"] = data.get("MEID", "")
            info["phone_number"] = data.get("Phone Number", "")
            info["udid"] = data.get("Target Identifier", data.get("Unique Identifier", ""))
            info["itunes_version"] = data.get("iTunes Version", "")
            info["guid"] = data.get("GUID", "")
            info["iccid"] = data.get("ICCID", "")
            last_backup = data.get("Last Backup Date")
            if isinstance(last_backup, datetime):
                info["last_backup_date"] = last_backup.strftime("%Y-%m-%d %H:%M:%S")
            # Installed apps from Info.plist
            installed_apps = data.get("Installed Applications", [])
            if installed_apps:
                info["installed_app_count"] = len(installed_apps)
            break
        except Exception:
            continue

    # Friendly model name
    product_type = info.get("product_type", "")
    info["friendly_model"] = PRODUCT_TYPE_MAP.get(product_type, product_type)

    # --- Manifest.plist ---
    for base in bases:
        manifest_plist = os.path.join(base, "Manifest.plist")
        if not os.path.isfile(manifest_plist):
            continue
        try:
            data = load_plist_file(manifest_plist)
            info["is_encrypted"] = data.get("IsEncrypted", False)
            info["was_passcode_set"] = data.get("WasPasscodeSet", False)

            lockdown = data.get("Lockdown", {})
            if lockdown:
                info.setdefault("device_name", lockdown.get("DeviceName", ""))
                info.setdefault(
                    "product_version", lockdown.get("ProductVersion", "")
                )
                info.setdefault("build_version", lockdown.get("BuildVersion", ""))
                info["device_class"] = lockdown.get("DeviceClass", "")
                info["hardware_model"] = lockdown.get("HardwareModel", "")
                info["product_name"] = lockdown.get("ProductName", "")
                info["unique_device_id"] = lockdown.get("UniqueDeviceID", "")

            # Application count from Manifest
            apps = data.get("Applications", {})
            if apps:
                info.setdefault("installed_app_count", len(apps))
            break
        except Exception:
            continue

    # --- Status.plist ---
    status_plist = os.path.join(backup_path, "Status.plist")
    if os.path.isfile(status_plist):
        try:
            data = load_plist_file(status_plist)
            date = data.get("Date")
            if isinstance(date, datetime):
                info.setdefault(
                    "last_backup_date", date.strftime("%Y-%m-%d %H:%M:%S")
                )
            info["backup_state"] = data.get("BackupState", "")
            info["snapshot_state"] = data.get("SnapshotState", "")
            info["is_full_backup"] = data.get("IsFullBackup", False)
            info["backup_version"] = str(data.get("Version", ""))
        except Exception:
            pass

    return info


def format_device_info(info: dict) -> list[tuple[str, str]]:
    """
    Format device info as a list of (label, value) tuples for display.
    Filters out empty values.
    """
    fields = [
        ("Device Name", info.get("device_name", "")),
        ("Model", info.get("friendly_model", info.get("product_type", ""))),
        ("Product Type", info.get("product_type", "")),
        ("iOS Version", info.get("product_version", "")),
        ("Build Version", info.get("build_version", "")),
        ("Serial Number", info.get("serial_number", "")),
        ("UDID", info.get("udid", "")),
        ("IMEI", info.get("imei", "")),
        ("MEID", info.get("meid", "")),
        ("ICCID", info.get("iccid", "")),
        ("Phone Number", info.get("phone_number", "")),
        ("", ""),  # Separator
        ("Encrypted Backup", "Yes" if info.get("is_encrypted") else "No"),
        ("Device Passcode Set", "Yes" if info.get("was_passcode_set") else "No"),
        ("Last Backup", info.get("last_backup_date", "")),
        ("Backup State", info.get("snapshot_state", info.get("backup_state", ""))),
        ("Full Backup", "Yes" if info.get("is_full_backup") else "No"),
        ("", ""),  # Separator
        ("Installed Apps", str(info.get("installed_app_count", "N/A"))),
        ("iTunes Version", info.get("itunes_version", "")),
        ("Hardware Model", info.get("hardware_model", "")),
    ]
    return [(label, value) for label, value in fields if label == "" or value]
