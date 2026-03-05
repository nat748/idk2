"""Safe plist loading for both binary and XML plists."""
import plistlib


def load_plist(data: bytes) -> dict:
    """Load a plist from bytes, handling both binary and XML formats."""
    try:
        return plistlib.loads(data)
    except Exception:
        # Try with different formats / fallback
        raise ValueError("Unable to parse plist data")


def load_plist_file(path: str) -> dict:
    """Load a plist from a file path."""
    with open(path, "rb") as f:
        return plistlib.load(f)
