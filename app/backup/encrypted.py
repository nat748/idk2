"""Encrypted backup decryption integration."""
import os
import sqlite3
import tempfile

from app.crypto.backup_decrypt import decrypt_file_data, unwrap_file_key
from app.crypto.keybag import Keybag


class EncryptedBackupHelper:
    """
    Manages decryption of encrypted iOS backups.

    Initialization:
    1. Parse BackupKeyBag from Manifest.plist
    2. Derive passkey from user password
    3. Unwrap class keys
    4. Optionally decrypt Manifest.db
    """

    def __init__(self, manifest_plist_data: dict, password: str):
        self.keybag = Keybag()
        self.unlocked = False
        self._decrypted_manifest_db_path: str | None = None

        keybag_data = manifest_plist_data.get("BackupKeyBag")
        if not keybag_data:
            return

        if isinstance(keybag_data, bytes):
            self.keybag.parse(keybag_data)
        else:
            return

        self.unlocked = self.keybag.unlock(password)

    def decrypt_file(
        self,
        encrypted_data: bytes,
        wrapped_key: bytes,
        protection_class: int,
    ) -> bytes:
        """Decrypt a single file from the backup."""
        if not self.unlocked:
            raise RuntimeError("Keybag not unlocked")

        file_key = unwrap_file_key(wrapped_key, protection_class, self.keybag)
        if not file_key:
            raise ValueError(
                f"Cannot unwrap file key for protection class {protection_class}"
            )

        return decrypt_file_data(encrypted_data, file_key)

    def decrypt_manifest_db(self, manifest_plist_data: dict, backup_path: str) -> str:
        """
        Decrypt Manifest.db and write to a temporary file.
        Returns the path to the decrypted database.
        """
        if not self.unlocked:
            raise RuntimeError("Keybag not unlocked")

        manifest_key = manifest_plist_data.get("ManifestKey")
        if not manifest_key:
            raise ValueError("ManifestKey not found in Manifest.plist")

        # ManifestKey is: 4-byte class + wrapped key
        if len(manifest_key) > 4:
            import struct

            key_class = struct.unpack("<I", manifest_key[:4])[0]
            wrapped = manifest_key[4:]
        else:
            raise ValueError("ManifestKey too short")

        file_key = unwrap_file_key(wrapped, key_class, self.keybag)
        if not file_key:
            raise ValueError("Failed to unwrap ManifestKey")

        # Find encrypted Manifest.db
        encrypted_path = None
        for base in [backup_path, os.path.join(backup_path, "Snapshot")]:
            p = os.path.join(base, "Manifest.db")
            if os.path.isfile(p):
                encrypted_path = p
                break

        if not encrypted_path:
            raise FileNotFoundError("Manifest.db not found")

        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()

        decrypted = decrypt_file_data(encrypted_data, file_key)

        # Write to temp file and verify it's valid SQLite
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        tmp.write(decrypted)
        tmp.close()

        # Verify it's a valid SQLite database
        try:
            conn = sqlite3.connect(tmp.name)
            conn.execute("SELECT COUNT(*) FROM Files")
            conn.close()
        except Exception:
            os.unlink(tmp.name)
            raise ValueError("Decrypted Manifest.db is not valid - wrong password?")

        self._decrypted_manifest_db_path = tmp.name
        return tmp.name

    def cleanup(self):
        """Remove temporary decrypted files."""
        if self._decrypted_manifest_db_path:
            try:
                os.unlink(self._decrypted_manifest_db_path)
            except OSError:
                pass
