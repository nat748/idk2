"""Utility to compute SHA-1 filenames used in iOS backups."""
import hashlib


def domain_path_to_hash(domain: str, relative_path: str) -> str:
    """
    Compute the SHA-1 hash used as filename in iOS backups.

    iOS backup convention: SHA1(domain + "-" + relativePath)
    File stored at: backup_root / hash[:2] / hash
    """
    combined = f"{domain}-{relative_path}"
    return hashlib.sha1(combined.encode("utf-8")).hexdigest()


def hash_to_path(backup_root: str, file_hash: str) -> str:
    """Convert a SHA-1 hash to the on-disk path within a backup."""
    import os

    return os.path.join(backup_root, file_hash[:2], file_hash)
