"""
Constants for iOS Backup Analyzer.
Backup paths, precomputed SHA-1 hashes, and device model mappings.
"""
import hashlib
import platform


def compute_backup_sha1(domain: str, relative_path: str) -> str:
    """Compute the SHA-1 filename used in iOS backups."""
    full = f"{domain}-{relative_path}"
    return hashlib.sha1(full.encode("utf-8")).hexdigest()


# --- Known file hashes (precomputed for direct lookup without Manifest.db) ---

RESTRICTIONS_PLIST = {
    "domain": "HomeDomain",
    "path": "Library/Preferences/com.apple.restrictionspassword.plist",
    "hash": compute_backup_sha1(
        "HomeDomain",
        "Library/Preferences/com.apple.restrictionspassword.plist",
    ),
}

SCREENTIME_PLISTS = [
    {
        "domain": "HomeDomain",
        "path": "Library/Preferences/com.apple.ScreenTime.plist",
        "hash": compute_backup_sha1(
            "HomeDomain",
            "Library/Preferences/com.apple.ScreenTime.plist",
        ),
    },
    {
        "domain": "HomeDomain",
        "path": "Library/Preferences/com.apple.ScreenTimeAgent.plist",
        "hash": compute_backup_sha1(
            "HomeDomain",
            "Library/Preferences/com.apple.ScreenTimeAgent.plist",
        ),
    },
    {
        "domain": "ManagedPreferencesDomain",
        "path": "mobile/Library/Preferences/com.apple.ScreenTime.plist",
        "hash": compute_backup_sha1(
            "ManagedPreferencesDomain",
            "mobile/Library/Preferences/com.apple.ScreenTime.plist",
        ),
    },
]

WIFI_PLISTS = [
    {
        "domain": "SystemPreferencesDomain",
        "path": "SystemConfiguration/com.apple.wifi.plist",
        "hash": compute_backup_sha1(
            "SystemPreferencesDomain",
            "SystemConfiguration/com.apple.wifi.plist",
        ),
    },
    {
        "domain": "SystemPreferencesDomain",
        "path": "SystemConfiguration/com.apple.wifi-networks.plist",
        "hash": compute_backup_sha1(
            "SystemPreferencesDomain",
            "SystemConfiguration/com.apple.wifi-networks.plist",
        ),
    },
]

KEYCHAIN_BACKUP = {
    "domain": "KeychainDomain",
    "path": "keychain-backup.plist",
    "hash": compute_backup_sha1("KeychainDomain", "keychain-backup.plist"),
}


# --- Backup locations per platform ---

WINDOWS_BACKUP_PATHS = [
    r"%USERPROFILE%\Apple\MobileSync\Backup",
    r"%APPDATA%\Apple Computer\MobileSync\Backup",
    r"%USERPROFILE%\AppData\Roaming\Apple Computer\MobileSync\Backup",
]

MACOS_BACKUP_PATHS = [
    "~/Library/Application Support/MobileSync/Backup",
]


def get_backup_search_paths() -> list[str]:
    """Return platform-appropriate backup search paths."""
    import os

    system = platform.system()
    if system == "Windows":
        return [os.path.expandvars(p) for p in WINDOWS_BACKUP_PATHS]
    elif system == "Darwin":
        return [os.path.expanduser(p) for p in MACOS_BACKUP_PATHS]
    return []


# --- Device model to friendly name mapping ---

PRODUCT_TYPE_MAP = {
    # iPhone
    "iPhone8,1": "iPhone 6s",
    "iPhone8,2": "iPhone 6s Plus",
    "iPhone8,4": "iPhone SE (1st gen)",
    "iPhone9,1": "iPhone 7",
    "iPhone9,2": "iPhone 7 Plus",
    "iPhone9,3": "iPhone 7",
    "iPhone9,4": "iPhone 7 Plus",
    "iPhone10,1": "iPhone 8",
    "iPhone10,2": "iPhone 8 Plus",
    "iPhone10,3": "iPhone X",
    "iPhone10,4": "iPhone 8",
    "iPhone10,5": "iPhone 8 Plus",
    "iPhone10,6": "iPhone X",
    "iPhone11,2": "iPhone XS",
    "iPhone11,4": "iPhone XS Max",
    "iPhone11,6": "iPhone XS Max",
    "iPhone11,8": "iPhone XR",
    "iPhone12,1": "iPhone 11",
    "iPhone12,3": "iPhone 11 Pro",
    "iPhone12,5": "iPhone 11 Pro Max",
    "iPhone12,8": "iPhone SE (2nd gen)",
    "iPhone13,1": "iPhone 12 mini",
    "iPhone13,2": "iPhone 12",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone14,4": "iPhone 13 mini",
    "iPhone14,5": "iPhone 13",
    "iPhone14,6": "iPhone SE (3rd gen)",
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone15,4": "iPhone 15",
    "iPhone15,5": "iPhone 15 Plus",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",
    "iPhone17,3": "iPhone 16",
    "iPhone17,4": "iPhone 16 Plus",
    # iPad
    "iPad6,11": "iPad (5th gen)",
    "iPad6,12": "iPad (5th gen)",
    "iPad7,5": "iPad (6th gen)",
    "iPad7,6": "iPad (6th gen)",
    "iPad7,11": "iPad (7th gen)",
    "iPad7,12": "iPad (7th gen)",
    "iPad11,6": "iPad (8th gen)",
    "iPad11,7": "iPad (8th gen)",
    "iPad12,1": "iPad (9th gen)",
    "iPad12,2": "iPad (9th gen)",
    "iPad13,18": "iPad (10th gen)",
    "iPad13,19": "iPad (10th gen)",
    "iPad8,1": "iPad Pro 11-inch (1st gen)",
    "iPad8,2": "iPad Pro 11-inch (1st gen)",
    "iPad8,3": "iPad Pro 11-inch (1st gen)",
    "iPad8,4": "iPad Pro 11-inch (1st gen)",
    "iPad8,9": "iPad Pro 11-inch (2nd gen)",
    "iPad8,10": "iPad Pro 11-inch (2nd gen)",
    "iPad13,4": "iPad Pro 11-inch (3rd gen)",
    "iPad13,5": "iPad Pro 11-inch (3rd gen)",
    "iPad14,3": "iPad Pro 11-inch (4th gen)",
    "iPad14,4": "iPad Pro 11-inch (4th gen)",
    "iPad8,5": "iPad Pro 12.9-inch (3rd gen)",
    "iPad8,6": "iPad Pro 12.9-inch (3rd gen)",
    "iPad8,11": "iPad Pro 12.9-inch (4th gen)",
    "iPad8,12": "iPad Pro 12.9-inch (4th gen)",
    "iPad13,8": "iPad Pro 12.9-inch (5th gen)",
    "iPad13,9": "iPad Pro 12.9-inch (5th gen)",
    "iPad14,5": "iPad Pro 12.9-inch (6th gen)",
    "iPad14,6": "iPad Pro 12.9-inch (6th gen)",
    "iPad11,1": "iPad mini (5th gen)",
    "iPad11,2": "iPad mini (5th gen)",
    "iPad14,1": "iPad mini (6th gen)",
    "iPad14,2": "iPad mini (6th gen)",
    "iPad11,3": "iPad Air (3rd gen)",
    "iPad11,4": "iPad Air (3rd gen)",
    "iPad13,1": "iPad Air (4th gen)",
    "iPad13,2": "iPad Air (4th gen)",
    "iPad13,16": "iPad Air (5th gen)",
    "iPad13,17": "iPad Air (5th gen)",
    # iPod touch
    "iPod9,1": "iPod touch (7th gen)",
}

# Keychain protection domain to protection class mapping
PDMN_TO_CLASS = {
    "ak": 6,    # kSecAttrAccessibleWhenUnlocked
    "ck": 7,    # kSecAttrAccessibleAfterFirstUnlock
    "dk": 8,    # kSecAttrAccessibleAlways (deprecated)
    "aku": 9,   # kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    "cku": 10,  # kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
    "dku": 11,  # kSecAttrAccessibleAlwaysThisDeviceOnly
    "akpu": 12, # kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly
}
