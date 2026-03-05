"""Keychain backup parser for extracting passwords and Screen Time data."""
import plistlib

from app.backup.backup_reader import BackupReader
from app.constants import KEYCHAIN_BACKUP, PDMN_TO_CLASS


# Screen Time keychain identifiers
SCREENTIME_SERVICES = {
    "com.apple.ScreenTime",
    "com.apple.ScreenTime.passcode",
    "com.apple.restrictionspassword",
    "com.apple.ScreenTime.ScreenTimePasscode",
}

SCREENTIME_ACCESS_GROUPS = {
    "com.apple.ScreenTime",
    "com.apple.screentime",
}


def parse_keychain_backup(reader: BackupReader) -> list[dict]:
    """
    Parse keychain-backup.plist and return all generic password entries.

    The keychain plist structure:
        Root dict with arrays:
        - 'genp': Generic passwords (kSecClassGenericPassword)
        - 'inet': Internet passwords
        - 'cert': Certificates
        - 'keys': Crypto keys

    Each genp entry:
        - acct: account name
        - svce: service name
        - agrp: access group
        - v_Data: password/value data (may be encrypted)
        - pdmn: protection domain
        - musr: user
    """
    entries = []

    try:
        data = reader.read_file(
            KEYCHAIN_BACKUP["domain"], KEYCHAIN_BACKUP["path"]
        )
        keychain = plistlib.loads(data)
    except FileNotFoundError:
        return []
    except Exception:
        return []

    # Parse generic passwords
    for entry in keychain.get("genp", []):
        if not isinstance(entry, dict):
            continue
        parsed = {
            "class": "genp",
            "acct": _decode_field(entry.get("acct", "")),
            "svce": _decode_field(entry.get("svce", "")),
            "agrp": _decode_field(entry.get("agrp", "")),
            "v_Data": entry.get("v_Data"),
            "pdmn": _decode_field(entry.get("pdmn", "")),
            "musr": _decode_field(entry.get("musr", "")),
            "cdat": entry.get("cdat"),  # Creation date
            "mdat": entry.get("mdat"),  # Modification date
        }
        entries.append(parsed)

    # Also check internet passwords
    for entry in keychain.get("inet", []):
        if not isinstance(entry, dict):
            continue
        parsed = {
            "class": "inet",
            "acct": _decode_field(entry.get("acct", "")),
            "svce": _decode_field(entry.get("srvr", "")),  # Server for inet
            "agrp": _decode_field(entry.get("agrp", "")),
            "v_Data": entry.get("v_Data"),
            "pdmn": _decode_field(entry.get("pdmn", "")),
            "port": entry.get("port", 0),
            "ptcl": _decode_field(entry.get("ptcl", "")),
        }
        entries.append(parsed)

    return entries


def find_screentime_entries(entries: list[dict]) -> list[dict]:
    """Find keychain entries related to Screen Time."""
    results = []
    for entry in entries:
        svce = entry.get("svce", "")
        agrp = entry.get("agrp", "")

        is_screentime = (
            svce in SCREENTIME_SERVICES
            or agrp in SCREENTIME_ACCESS_GROUPS
            or "ScreenTime" in svce
            or "ScreenTime" in agrp
            or "screentime" in svce.lower()
            or "restrictions" in svce.lower()
        )

        if is_screentime:
            results.append(entry)

    return results


def _decode_field(value) -> str:
    """Decode a keychain field that may be bytes or string."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    if isinstance(value, str):
        return value
    return str(value) if value else ""
