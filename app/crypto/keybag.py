"""iOS backup keybag parser for encrypted backup decryption."""
import hashlib
import struct

from app.crypto.aes_unwrap import aes_unwrap_key


class ClassKey:
    """A single protection class key from the keybag."""

    def __init__(self):
        self.clas: int = 0
        self.wrap: int = 0
        self.wpky: bytes = b""  # Wrapped per-class key
        self.key: bytes = b""   # Unwrapped key (after unlock)
        self.uuid: bytes = b""


class Keybag:
    """
    Parse and manage iOS backup keybag.

    The keybag is stored as a TLV (Type-Length-Value) blob in
    Manifest.plist -> BackupKeyBag.

    TLV format:
        4-byte tag (e.g. b'SALT', b'ITER', b'UUID', b'CLAS', b'WPKY')
        4-byte big-endian length
        <length> bytes of value
    """

    def __init__(self):
        self.uuid: bytes = b""
        self.hmck: bytes = b""
        self.salt: bytes = b""
        self.iterations: int = 0
        self.type: int = 0
        self.version: int = 0
        self.class_keys: dict[int, ClassKey] = {}
        self.unlocked: bool = False
        self._dpsl: bytes = b""  # Double-protection salt (iOS 10.2+)
        self._dpic: int = 0      # Double-protection iteration count

    def parse(self, data: bytes):
        """Parse TLV-encoded keybag data."""
        offset = 0
        current_class_key = None

        while offset + 8 <= len(data):
            tag = data[offset : offset + 4]
            length = struct.unpack(">I", data[offset + 4 : offset + 8])[0]
            offset += 8

            if offset + length > len(data):
                break

            value = data[offset : offset + length]
            offset += length

            tag_str = tag.decode("ascii", errors="replace")

            if tag_str == "UUID":
                if current_class_key is None:
                    self.uuid = value
                else:
                    current_class_key.uuid = value
            elif tag_str == "HMCK":
                self.hmck = value
            elif tag_str == "SALT":
                self.salt = value
            elif tag_str == "ITER":
                self.iterations = struct.unpack(">I", value)[0]
            elif tag_str == "TYPE":
                self.type = struct.unpack(">I", value)[0]
            elif tag_str == "VERS":
                self.version = struct.unpack(">I", value)[0]
            elif tag_str == "DPSL":
                self._dpsl = value
            elif tag_str == "DPIC":
                self._dpic = struct.unpack(">I", value)[0]
            elif tag_str == "CLAS":
                # Start of a new class key
                clas = struct.unpack(">I", value)[0]
                current_class_key = ClassKey()
                current_class_key.clas = clas
                self.class_keys[clas] = current_class_key
            elif tag_str == "WRAP":
                if current_class_key:
                    current_class_key.wrap = struct.unpack(">I", value)[0]
            elif tag_str == "WPKY":
                if current_class_key:
                    current_class_key.wpky = value
            elif tag_str == "KTYP":
                pass  # Key type, informational
            elif tag_str == "PBKY":
                pass  # Public key, not needed for backup decryption

    def unlock(self, password: str) -> bool:
        """
        Derive the backup passkey from the password and unwrap all class keys.

        iOS 10.2+ uses double PBKDF2:
            1. PBKDF2-SHA256(password, dpsl, dpic) -> intermediate
            2. PBKDF2-SHA1(intermediate, salt, iter) -> passkey

        Earlier versions:
            PBKDF2-SHA1(password, salt, iter) -> passkey

        Returns True if successful.
        """
        password_bytes = password.encode("utf-8")

        # iOS 10.2+ double protection
        if self._dpsl and self._dpic:
            intermediate = hashlib.pbkdf2_hmac(
                "sha256", password_bytes, self._dpsl, self._dpic, dklen=32
            )
            passkey = hashlib.pbkdf2_hmac(
                "sha1", intermediate, self.salt, self.iterations, dklen=32
            )
        else:
            passkey = hashlib.pbkdf2_hmac(
                "sha1", password_bytes, self.salt, self.iterations, dklen=32
            )

        # Unwrap each class key
        success_count = 0
        for clas, class_key in self.class_keys.items():
            if class_key.wrap == 0:
                # Not wrapped, key is plaintext
                class_key.key = class_key.wpky
                success_count += 1
                continue

            if not class_key.wpky or len(class_key.wpky) < 24:
                continue

            try:
                unwrapped = aes_unwrap_key(passkey, class_key.wpky)
                class_key.key = unwrapped
                success_count += 1
            except ValueError:
                # Wrong password or corrupted key
                continue

        self.unlocked = success_count > 0
        return self.unlocked

    def get_class_key(self, protection_class: int) -> bytes | None:
        """Get the unwrapped key for a protection class."""
        ck = self.class_keys.get(protection_class)
        if ck and ck.key:
            return ck.key
        return None
