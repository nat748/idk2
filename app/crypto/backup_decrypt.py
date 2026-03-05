"""Full encrypted backup decryption pipeline."""
import hashlib

from Crypto.Cipher import AES

from app.crypto.aes_unwrap import aes_unwrap_key
from app.crypto.keybag import Keybag


def decrypt_file_data(
    encrypted_data: bytes,
    file_key: bytes,
) -> bytes:
    """
    Decrypt a single backup file using AES-CBC.

    iOS encrypted backup files use:
    - AES-256-CBC
    - Zero IV (16 null bytes)
    - PKCS7 padding (or no padding if exact block size)
    """
    if not file_key:
        return encrypted_data

    # Use first 32 bytes as AES key, zero IV
    key = file_key[:32] if len(file_key) >= 32 else file_key.ljust(32, b"\x00")
    iv = b"\x00" * 16

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_data)

    # Remove PKCS7 padding
    if decrypted:
        padding_len = decrypted[-1]
        if 0 < padding_len <= 16:
            # Verify padding
            if all(b == padding_len for b in decrypted[-padding_len:]):
                decrypted = decrypted[:-padding_len]

    return decrypted


def unwrap_file_key(
    wrapped_key: bytes,
    protection_class: int,
    keybag: Keybag,
) -> bytes | None:
    """
    Unwrap a per-file encryption key using the appropriate class key.

    Args:
        wrapped_key: The wrapped per-file key from Manifest.db file blob.
        protection_class: The protection class for this file.
        keybag: Unlocked keybag with class keys.

    Returns:
        Unwrapped file key, or None if the class key is not available.
    """
    class_key = keybag.get_class_key(protection_class)
    if not class_key:
        return None

    if len(wrapped_key) < 24:
        return None

    try:
        return aes_unwrap_key(class_key, wrapped_key)
    except ValueError:
        return None


def decrypt_manifest_db(
    encrypted_db_path: str,
    manifest_key_data: bytes,
    manifest_key_class: int,
    keybag: Keybag,
) -> bytes:
    """
    Decrypt Manifest.db from an encrypted backup.

    The ManifestKey from Manifest.plist is a wrapped key that needs to be
    unwrapped using the keybag's class key, then used to decrypt the db.
    """
    # The manifest key data starts with a 4-byte class prefix
    if len(manifest_key_data) > 4:
        wrapped_key = manifest_key_data[4:]
    else:
        wrapped_key = manifest_key_data

    file_key = unwrap_file_key(wrapped_key, manifest_key_class, keybag)
    if not file_key:
        raise ValueError(
            f"Cannot unwrap ManifestKey with protection class {manifest_key_class}"
        )

    with open(encrypted_db_path, "rb") as f:
        encrypted_data = f.read()

    return decrypt_file_data(encrypted_data, file_key)
