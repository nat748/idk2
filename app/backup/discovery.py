"""Auto-detect iOS backup locations on the filesystem."""
import os
import re
from dataclasses import dataclass, field
from datetime import datetime

from app.constants import get_backup_search_paths
from app.utils.plist_utils import load_plist_file


@dataclass
class BackupInfo:
    """Metadata about a discovered iOS backup."""

    path: str
    udid: str = ""
    device_name: str = "Unknown"
    product_version: str = ""
    backup_date: datetime | None = None
    is_encrypted: bool = False
    is_complete: bool = True
    snapshot_state: str = ""

    @property
    def display_name(self) -> str:
        parts = [self.device_name]
        if self.product_version:
            parts.append(f"iOS {self.product_version}")
        if self.backup_date:
            parts.append(self.backup_date.strftime("%Y-%m-%d %H:%M"))
        if not self.is_complete:
            parts.append("(incomplete)")
        return " — ".join(parts)


# UDID patterns: 40 hex chars or newer format like 00008120-XXXXXXXXXXXX
_UDID_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$|^[0-9A-F]{8}-[0-9A-F]{16}$")


def discover_backups(extra_paths: list[str] | None = None) -> list[BackupInfo]:
    """
    Scan known filesystem locations for iOS backups.
    Returns a list of BackupInfo objects sorted by backup date (newest first).
    """
    search_paths = get_backup_search_paths()
    if extra_paths:
        search_paths.extend(extra_paths)

    backups = []
    seen_paths = set()

    for search_dir in search_paths:
        if not os.path.isdir(search_dir):
            continue
        try:
            for entry in os.scandir(search_dir):
                if not entry.is_dir():
                    continue
                if entry.path in seen_paths:
                    continue
                # Check if directory name looks like a UDID
                if not _UDID_PATTERN.match(entry.name):
                    continue
                seen_paths.add(entry.path)
                info = _probe_backup(entry.path, entry.name)
                if info:
                    backups.append(info)
        except PermissionError:
            continue

    backups.sort(key=lambda b: b.backup_date or datetime.min, reverse=True)
    return backups


def probe_backup_path(path: str) -> BackupInfo | None:
    """Probe a user-specified path as an iOS backup."""
    if not os.path.isdir(path):
        return None
    udid = os.path.basename(path)
    return _probe_backup(path, udid)


def _probe_backup(backup_path: str, udid: str) -> BackupInfo | None:
    """Attempt to read backup metadata from a directory."""
    info = BackupInfo(path=backup_path, udid=udid)

    # Check both root and Snapshot/ subdirectory
    bases = [backup_path, os.path.join(backup_path, "Snapshot")]

    for base in bases:
        # Info.plist
        info_plist = os.path.join(base, "Info.plist")
        if os.path.isfile(info_plist):
            try:
                data = load_plist_file(info_plist)
                info.device_name = data.get(
                    "Device Name", data.get("Display Name", "Unknown")
                )
                info.product_version = data.get("Product Version", "")
                last_backup = data.get("Last Backup Date")
                if isinstance(last_backup, datetime):
                    info.backup_date = last_backup
            except Exception:
                pass

        # Manifest.plist
        manifest_plist = os.path.join(base, "Manifest.plist")
        if os.path.isfile(manifest_plist):
            try:
                data = load_plist_file(manifest_plist)
                info.is_encrypted = data.get("IsEncrypted", False)
            except Exception:
                pass

    # Status.plist (always at root)
    status_plist = os.path.join(backup_path, "Status.plist")
    if os.path.isfile(status_plist):
        try:
            data = load_plist_file(status_plist)
            date = data.get("Date")
            if isinstance(date, datetime) and not info.backup_date:
                info.backup_date = date
            info.snapshot_state = data.get("SnapshotState", "")
            if info.snapshot_state and info.snapshot_state != "finished":
                info.is_complete = False
        except Exception:
            pass

    # Verify this looks like a real backup (has Manifest.db or hex subdirs)
    has_manifest = any(
        os.path.isfile(os.path.join(b, "Manifest.db")) for b in bases
    )
    has_hex_dirs = any(
        os.path.isdir(os.path.join(backup_path, f"{i:02x}")) for i in range(16)
    )
    if not has_manifest and not has_hex_dirs:
        return None

    return info
