"""iOS 12+ Screen Time passcode extraction (multi-strategy)."""
from app.backup.backup_reader import BackupReader
from app.crypto.pbkdf2_crack import crack_pin_multi


# All known locations where Screen Time passcode data may be stored
SCREENTIME_PATHS = [
    ("HomeDomain", "Library/Preferences/com.apple.ScreenTime.plist"),
    ("HomeDomain", "Library/Preferences/com.apple.ScreenTimeAgent.plist"),
    (
        "ManagedPreferencesDomain",
        "mobile/Library/Preferences/com.apple.ScreenTime.plist",
    ),
    (
        "ManagedPreferencesDomain",
        "mobile/Library/Preferences/com.apple.ScreenTimeAgent.plist",
    ),
]

# Known key paths within the plist for hash and salt
HASH_KEY_PATHS = [
    # iOS 12-13 style
    (["passcode", "value"], ["passcode", "salt"]),
    (["passcode", "hash"], ["passcode", "salt"]),
    # iOS 14+ style
    (["user", "passcodeHash"], ["user", "passcodeSalt"]),
    (["user", "passcode", "hash"], ["user", "passcode", "salt"]),
    # Direct keys
    (["passcodeHash"], ["passcodeSalt"]),
    (["PasscodeHash"], ["PasscodeSalt"]),
    (["RestrictionsPasswordKey"], ["RestrictionsPasswordSalt"]),
]

# Keys that may directly contain the passcode
DIRECT_PASSCODE_KEYS = [
    ["passcode"],
    ["user", "passcode"],
    ["Passcode"],
]

# Keychain service names for Screen Time
KEYCHAIN_SERVICES = [
    "com.apple.ScreenTime",
    "com.apple.ScreenTime.passcode",
    "com.apple.restrictionspassword",
    "com.apple.ScreenTime.ScreenTimePasscode",
]


def extract_screentime_passcode(
    reader: BackupReader,
    progress_callback=None,
) -> dict:
    """
    Multi-strategy Screen Time passcode extraction for iOS 12+.

    Strategy:
    1. Try each known plist location
    2. For each plist, try all known key paths for hash+salt
    3. Check for direct passcode value
    4. If encrypted backup, search keychain
    5. Brute force any found hashes

    Returns dict with: found, passcode, method, source_file, time_taken, error, details
    """
    result = {
        "found": False,
        "passcode": None,
        "method": "screentime",
        "ios_range": "iOS 12+",
        "source_file": None,
        "time_taken": 0.0,
        "error": None,
        "details": [],
    }

    # Strategy 1 & 2: Plist-based extraction
    for domain, path in SCREENTIME_PATHS:
        try:
            plist = reader.read_plist(domain, path)
            result["details"].append(f"Found: {domain}/{path}")
        except FileNotFoundError:
            continue
        except Exception as e:
            result["details"].append(f"Error reading {path}: {e}")
            continue

        # Try direct passcode first
        direct = _try_direct_passcode(plist)
        if direct:
            result["found"] = True
            result["passcode"] = direct
            result["source_file"] = path
            result["method"] = "screentime_direct"
            return result

        # Try hash+salt extraction
        hash_data, salt_data = _extract_hash_salt(plist)
        if hash_data and salt_data:
            result["source_file"] = path
            result["details"].append(
                f"Found hash ({len(hash_data)} bytes) + salt ({len(salt_data)} bytes)"
            )

            # Determine iteration count and algorithm
            iterations = _detect_iterations(plist)
            hash_algo = _detect_hash_algo(plist, hash_data)
            dk_len = len(hash_data)

            pin, digits, elapsed = crack_pin_multi(
                target_hash=hash_data,
                salt=salt_data,
                iterations=iterations,
                hash_algo=hash_algo,
                dk_len=dk_len,
                progress_callback=progress_callback,
            )
            result["time_taken"] = elapsed
            if pin:
                result["found"] = True
                result["passcode"] = pin
                result["method"] = f"screentime_brute_{digits}digit"
                return result
            result["details"].append("Brute force failed for this hash")

    # Strategy 3: Keychain (encrypted backups)
    if reader.is_encrypted:
        keychain_result = _try_keychain_extraction(reader, progress_callback)
        if keychain_result and keychain_result.get("found"):
            return keychain_result
        if keychain_result:
            result["details"].extend(keychain_result.get("details", []))

    if not result["found"] and not result["error"]:
        if result["details"]:
            result["error"] = "Screen Time data found but passcode could not be recovered"
        else:
            result["error"] = (
                "No Screen Time passcode data found. The passcode may be stored "
                "in the device keychain (requires encrypted backup with password)."
            )

    return result


def _traverse_keys(data: dict, keys: list[str]):
    """Traverse nested dict using a list of keys."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def _try_direct_passcode(plist: dict) -> str | None:
    """Check if the plist contains the passcode directly as a string."""
    for key_path in DIRECT_PASSCODE_KEYS:
        value = _traverse_keys(plist, key_path)
        if isinstance(value, str) and value.isdigit() and 4 <= len(value) <= 6:
            return value
        if isinstance(value, int) and 0 <= value <= 999999:
            return str(value).zfill(4) if value <= 9999 else str(value).zfill(6)
    return None


def _extract_hash_salt(plist: dict) -> tuple[bytes | None, bytes | None]:
    """Try all known key paths to find hash and salt."""
    for hash_keys, salt_keys in HASH_KEY_PATHS:
        hash_val = _traverse_keys(plist, hash_keys)
        salt_val = _traverse_keys(plist, salt_keys)
        if isinstance(hash_val, bytes) and isinstance(salt_val, bytes):
            return hash_val, salt_val
    return None, None


def _detect_iterations(plist: dict) -> int:
    """Detect PBKDF2 iteration count from plist data."""
    for key_path in [
        ["passcode", "iterations"],
        ["user", "passcodeIterations"],
        ["iterations"],
    ]:
        val = _traverse_keys(plist, key_path)
        if isinstance(val, int) and val > 0:
            return val
    return 1000  # Default


def _detect_hash_algo(plist: dict, hash_data: bytes) -> str:
    """Detect hash algorithm based on hash length and plist hints."""
    if len(hash_data) == 32:
        return "sha256"
    if len(hash_data) == 64:
        return "sha512"
    return "sha1"  # 20 bytes = SHA1


def _try_keychain_extraction(reader: BackupReader, progress_callback=None) -> dict:
    """Try to extract Screen Time passcode from keychain."""
    result = {
        "found": False,
        "passcode": None,
        "method": "screentime_keychain",
        "ios_range": "iOS 12+",
        "source_file": "keychain-backup.plist",
        "time_taken": 0.0,
        "error": None,
        "details": [],
    }

    try:
        from app.extractors.keychain import (
            parse_keychain_backup,
            find_screentime_entries,
        )

        entries = parse_keychain_backup(reader)
        if not entries:
            result["details"].append("Keychain: no entries found or not decryptable")
            return result

        st_entries = find_screentime_entries(entries)
        if not st_entries:
            result["details"].append("Keychain: no Screen Time entries found")
            return result

        for entry in st_entries:
            result["details"].append(
                f"Keychain: found entry svce={entry.get('svce', 'N/A')}"
            )
            v_data = entry.get("v_Data")
            if isinstance(v_data, bytes):
                # v_Data might be the passcode directly
                try:
                    passcode = v_data.decode("utf-8").strip()
                    if passcode.isdigit() and 4 <= len(passcode) <= 6:
                        result["found"] = True
                        result["passcode"] = passcode
                        return result
                except UnicodeDecodeError:
                    pass
            elif isinstance(v_data, str):
                if v_data.isdigit() and 4 <= len(v_data) <= 6:
                    result["found"] = True
                    result["passcode"] = v_data
                    return result

    except ImportError:
        result["details"].append("Keychain module not available")
    except Exception as e:
        result["details"].append(f"Keychain extraction error: {e}")

    return result
