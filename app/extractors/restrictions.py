"""iOS 2-11 Restrictions passcode extraction."""
from app.backup.backup_reader import BackupReader
from app.crypto.pbkdf2_crack import crack_pin_multi


RESTRICTIONS_DOMAIN = "HomeDomain"
RESTRICTIONS_PATH = "Library/Preferences/com.apple.restrictionspassword.plist"


def extract_restrictions_passcode(
    reader: BackupReader,
    progress_callback=None,
) -> dict:
    """
    Extract and crack the Restrictions passcode (iOS 2-11).

    The plist contains:
        RestrictionsPasswordKey: <20 bytes> (PBKDF2-SHA1 derived key)
        RestrictionsPasswordSalt: <4 bytes> (salt)

    Returns dict with: found, passcode, method, ios_range, time_taken, error
    """
    result = {
        "found": False,
        "passcode": None,
        "method": "restrictions_plist",
        "ios_range": "iOS 2-11",
        "time_taken": 0.0,
        "error": None,
    }

    try:
        plist = reader.read_plist(RESTRICTIONS_DOMAIN, RESTRICTIONS_PATH)
    except FileNotFoundError:
        result["error"] = "Restrictions plist not found (normal for iOS 12+)"
        return result
    except Exception as e:
        result["error"] = f"Failed to read restrictions plist: {e}"
        return result

    key = plist.get("RestrictionsPasswordKey")
    salt = plist.get("RestrictionsPasswordSalt")

    if not key or not salt:
        result["error"] = "Restrictions plist found but missing password hash or salt"
        return result

    if isinstance(key, bytes) and isinstance(salt, bytes):
        pin, digits, elapsed = crack_pin_multi(
            target_hash=key,
            salt=salt,
            iterations=1000,
            hash_algo="sha1",
            dk_len=20,
            progress_callback=progress_callback,
        )
        result["time_taken"] = elapsed
        if pin:
            result["found"] = True
            result["passcode"] = pin
        else:
            result["error"] = "Hash found but could not crack passcode"
    else:
        result["error"] = "Unexpected data types in restrictions plist"

    return result
