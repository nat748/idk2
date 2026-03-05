"""Parse Manifest.db from iOS backups for file lookup."""
import os
import sqlite3

from app.utils.sha1_filename import domain_path_to_hash


class ManifestDB:
    """
    Interface to Manifest.db in an iOS backup.

    The Files table schema:
        fileID TEXT PRIMARY KEY  -- SHA-1 hash (on-disk filename)
        domain TEXT              -- e.g. "HomeDomain", "AppDomain-com.example"
        relativePath TEXT        -- e.g. "Library/Preferences/com.apple.foo.plist"
        flags INTEGER
        file BLOB               -- binary plist with file metadata
    """

    def __init__(self, backup_path: str):
        self.backup_path = backup_path
        self._db_path = self._find_manifest_db()
        self._conn: sqlite3.Connection | None = None

    def _find_manifest_db(self) -> str | None:
        """Find Manifest.db in backup root or Snapshot/ subdirectory."""
        for base in [self.backup_path, os.path.join(self.backup_path, "Snapshot")]:
            path = os.path.join(base, "Manifest.db")
            if os.path.isfile(path):
                return path
        return None

    @property
    def available(self) -> bool:
        return self._db_path is not None

    def open(self):
        """Open the database connection."""
        if not self._db_path:
            raise FileNotFoundError("Manifest.db not found in backup")
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def lookup(self, domain: str, relative_path: str) -> str | None:
        """Look up a file's hash ID by domain and relative path."""
        if not self._conn:
            raise RuntimeError("Database not open")
        cursor = self._conn.execute(
            "SELECT fileID FROM Files WHERE domain=? AND relativePath=?",
            (domain, relative_path),
        )
        row = cursor.fetchone()
        return row["fileID"] if row else None

    def lookup_like(self, domain_pattern: str, path_pattern: str) -> list[dict]:
        """Look up files using LIKE patterns."""
        if not self._conn:
            raise RuntimeError("Database not open")
        cursor = self._conn.execute(
            "SELECT fileID, domain, relativePath FROM Files "
            "WHERE domain LIKE ? AND relativePath LIKE ?",
            (domain_pattern, path_pattern),
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_domains(self) -> list[str]:
        """List all unique domains in the backup."""
        if not self._conn:
            raise RuntimeError("Database not open")
        cursor = self._conn.execute("SELECT DISTINCT domain FROM Files ORDER BY domain")
        return [row["domain"] for row in cursor.fetchall()]

    def list_files(self, domain: str | None = None, limit: int = 1000) -> list[dict]:
        """List files, optionally filtered by domain."""
        if not self._conn:
            raise RuntimeError("Database not open")
        if domain:
            cursor = self._conn.execute(
                "SELECT fileID, domain, relativePath FROM Files "
                "WHERE domain=? ORDER BY relativePath LIMIT ?",
                (domain, limit),
            )
        else:
            cursor = self._conn.execute(
                "SELECT fileID, domain, relativePath FROM Files "
                "ORDER BY domain, relativePath LIMIT ?",
                (limit,),
            )
        return [dict(row) for row in cursor.fetchall()]

    def count_files(self, domain: str | None = None) -> int:
        """Count files, optionally filtered by domain."""
        if not self._conn:
            raise RuntimeError("Database not open")
        if domain:
            cursor = self._conn.execute(
                "SELECT COUNT(*) as cnt FROM Files WHERE domain=?", (domain,)
            )
        else:
            cursor = self._conn.execute("SELECT COUNT(*) as cnt FROM Files")
        return cursor.fetchone()["cnt"]

    def file_on_disk(self, file_id: str) -> str:
        """Convert a file ID to its on-disk path."""
        return os.path.join(self.backup_path, file_id[:2], file_id)


class ManifestFallback:
    """
    Fallback for backups without Manifest.db.
    Uses precomputed SHA-1 hashes to locate files directly.
    """

    def __init__(self, backup_path: str):
        self.backup_path = backup_path

    def lookup(self, domain: str, relative_path: str) -> str | None:
        """Look up a file using computed hash, checking if it exists on disk."""
        file_hash = domain_path_to_hash(domain, relative_path)
        file_path = os.path.join(self.backup_path, file_hash[:2], file_hash)
        if os.path.isfile(file_path):
            return file_hash
        return None

    def file_on_disk(self, file_id: str) -> str:
        return os.path.join(self.backup_path, file_id[:2], file_id)
