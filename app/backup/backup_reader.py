"""Unified interface to read files from an iOS backup."""
import os

from app.backup.manifest import ManifestDB, ManifestFallback
from app.utils.plist_utils import load_plist, load_plist_file


class BackupReader:
    """
    High-level interface to read any file from an iOS backup.

    Handles:
    - Manifest.db lookup or fallback to precomputed hashes
    - Encrypted backup decryption (when password provided)
    - Both root-level and Snapshot/ layouts
    """

    def __init__(self, backup_path: str, password: str | None = None):
        self.backup_path = backup_path
        self.password = password
        self._manifest_db: ManifestDB | None = None
        self._manifest_fallback: ManifestFallback | None = None
        self._is_encrypted: bool = False
        self._keybag = None
        self._class_keys: dict | None = None
        self._device_info: dict = {}

        self._init_manifest()
        self._load_root_info()
        if self._is_encrypted and password:
            self._init_decryption()

    def _init_manifest(self):
        """Initialize Manifest.db or fallback."""
        db = ManifestDB(self.backup_path)
        if db.available:
            self._manifest_db = db
            self._manifest_db.open()
        else:
            self._manifest_fallback = ManifestFallback(self.backup_path)

    def _load_root_info(self):
        """Load root-level plist files for backup metadata."""
        for base in [self.backup_path, os.path.join(self.backup_path, "Snapshot")]:
            manifest_plist = os.path.join(base, "Manifest.plist")
            if os.path.isfile(manifest_plist):
                try:
                    data = load_plist_file(manifest_plist)
                    self._is_encrypted = data.get("IsEncrypted", False)
                    self._manifest_plist_data = data
                except Exception:
                    self._manifest_plist_data = {}
                break
        else:
            self._manifest_plist_data = {}

        for base in [self.backup_path, os.path.join(self.backup_path, "Snapshot")]:
            info_plist = os.path.join(base, "Info.plist")
            if os.path.isfile(info_plist):
                try:
                    self._device_info = load_plist_file(info_plist)
                except Exception:
                    pass
                break

    def _init_decryption(self):
        """Initialize encrypted backup decryption."""
        try:
            from app.backup.encrypted import EncryptedBackupHelper

            self._encryption_helper = EncryptedBackupHelper(
                self._manifest_plist_data, self.password
            )
            if self._encryption_helper.unlocked:
                # If Manifest.db is encrypted, decrypt it
                if self._manifest_db is None:
                    self._decrypt_manifest_db()
        except Exception:
            self._encryption_helper = None

    def _decrypt_manifest_db(self):
        """Decrypt Manifest.db for encrypted backups."""
        # Will be implemented in encrypted.py
        pass

    @property
    def is_encrypted(self) -> bool:
        return self._is_encrypted

    @property
    def ios_version(self) -> str:
        return self._device_info.get("Product Version", "")

    @property
    def ios_major(self) -> int:
        try:
            return int(self.ios_version.split(".")[0])
        except (ValueError, IndexError):
            return 0

    @property
    def device_name(self) -> str:
        return self._device_info.get(
            "Device Name", self._device_info.get("Display Name", "Unknown")
        )

    def lookup_file_id(self, domain: str, relative_path: str) -> str | None:
        """Find the file ID for a domain/path pair."""
        if self._manifest_db:
            return self._manifest_db.lookup(domain, relative_path)
        elif self._manifest_fallback:
            return self._manifest_fallback.lookup(domain, relative_path)
        return None

    def read_file(self, domain: str, relative_path: str) -> bytes:
        """
        Read a file from the backup by domain and relative path.
        Raises FileNotFoundError if the file doesn't exist.
        """
        file_id = self.lookup_file_id(domain, relative_path)
        if not file_id:
            raise FileNotFoundError(
                f"File not found in backup: {domain}/{relative_path}"
            )
        return self.read_file_by_id(file_id, domain, relative_path)

    def read_file_by_id(
        self, file_id: str, domain: str = "", relative_path: str = ""
    ) -> bytes:
        """Read a file from backup by its file ID (SHA-1 hash)."""
        if self._manifest_db:
            file_path = self._manifest_db.file_on_disk(file_id)
        else:
            file_path = self._manifest_fallback.file_on_disk(file_id)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Backup file not found on disk: {file_path}")

        with open(file_path, "rb") as f:
            data = f.read()

        # Decrypt if needed
        if self._is_encrypted and self.password and hasattr(self, "_encryption_helper"):
            if self._encryption_helper and self._encryption_helper.unlocked:
                try:
                    protection_class, wrapped_key = self._get_file_encryption_info(
                        file_id
                    )
                    if wrapped_key:
                        data = self._encryption_helper.decrypt_file(
                            data, wrapped_key, protection_class
                        )
                except Exception:
                    pass  # Return raw data if decryption fails

        return data

    def _get_file_encryption_info(self, file_id: str) -> tuple[int, bytes | None]:
        """Get encryption info for a file from Manifest.db."""
        if not self._manifest_db or not self._manifest_db._conn:
            return 0, None
        cursor = self._manifest_db._conn.execute(
            "SELECT file FROM Files WHERE fileID=?", (file_id,)
        )
        row = cursor.fetchone()
        if not row or not row["file"]:
            return 0, None
        try:
            import plistlib

            file_meta = plistlib.loads(row["file"])
            objects = file_meta.get("$objects", [])
            # Parse NSKeyedArchiver format for EncryptionKey and ProtectionClass
            protection_class = 0
            encryption_key = None
            for obj in objects:
                if isinstance(obj, dict):
                    if "ProtectionClass" in obj:
                        protection_class = obj["ProtectionClass"]
                    if "EncryptionKey" in obj:
                        enc_key_data = obj["EncryptionKey"]
                        if isinstance(enc_key_data, bytes):
                            # Skip the first 4 bytes (class key length prefix)
                            encryption_key = enc_key_data[4:]
            return protection_class, encryption_key
        except Exception:
            return 0, None

    def read_plist(self, domain: str, relative_path: str) -> dict:
        """Read and parse a plist file from the backup."""
        data = self.read_file(domain, relative_path)
        return load_plist(data)

    def list_domains(self) -> list[str]:
        """List all domains in the backup."""
        if self._manifest_db:
            return self._manifest_db.list_domains()
        return []

    def list_files(self, domain: str | None = None, limit: int = 1000) -> list[dict]:
        """List files in the backup."""
        if self._manifest_db:
            return self._manifest_db.list_files(domain, limit)
        return []

    def close(self):
        if self._manifest_db:
            self._manifest_db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
