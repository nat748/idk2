"""RFC 3394 AES Key Unwrap implementation."""
import struct

from Crypto.Cipher import AES


# Default IV per RFC 3394
_DEFAULT_IV = b"\xa6\xa6\xa6\xa6\xa6\xa6\xa6\xa6"


def aes_unwrap_key(kek: bytes, wrapped: bytes) -> bytes:
    """
    RFC 3394 AES Key Unwrap.

    Args:
        kek: Key Encryption Key (16, 24, or 32 bytes).
        wrapped: Wrapped key data (must be multiple of 8 bytes, min 24 bytes).

    Returns:
        Unwrapped key bytes.

    Raises:
        ValueError: If integrity check fails or invalid input.
    """
    if len(wrapped) % 8 != 0:
        raise ValueError("Wrapped key length must be a multiple of 8 bytes")
    if len(wrapped) < 24:
        raise ValueError("Wrapped key must be at least 24 bytes")

    n = len(wrapped) // 8 - 1
    cipher = AES.new(kek, AES.MODE_ECB)

    # Initialize
    a = bytearray(wrapped[:8])
    r = [bytearray(wrapped[i * 8 : (i + 1) * 8]) for i in range(1, n + 1)]

    # Unwrap
    for j in range(5, -1, -1):
        for i in range(n, 0, -1):
            # Compute t = n*j + i
            t = n * j + i
            t_bytes = struct.pack(">Q", t)
            # XOR A with t
            a_xor = bytearray(a[k] ^ t_bytes[k] for k in range(8))
            # Decrypt
            b = cipher.decrypt(bytes(a_xor + r[i - 1]))
            a = bytearray(b[:8])
            r[i - 1] = bytearray(b[8:])

    # Integrity check
    if bytes(a) != _DEFAULT_IV:
        raise ValueError(
            "AES key unwrap integrity check failed - wrong password or corrupted data"
        )

    return b"".join(bytes(block) for block in r)


def aes_wrap_key(kek: bytes, plaintext: bytes) -> bytes:
    """
    RFC 3394 AES Key Wrap (for testing purposes).

    Args:
        kek: Key Encryption Key.
        plaintext: Key data to wrap (must be multiple of 8 bytes).

    Returns:
        Wrapped key bytes.
    """
    if len(plaintext) % 8 != 0:
        raise ValueError("Plaintext length must be a multiple of 8 bytes")

    n = len(plaintext) // 8
    cipher = AES.new(kek, AES.MODE_ECB)

    a = bytearray(_DEFAULT_IV)
    r = [bytearray(plaintext[i * 8 : (i + 1) * 8]) for i in range(n)]

    for j in range(6):
        for i in range(n):
            b = cipher.encrypt(bytes(a + r[i]))
            t = struct.pack(">Q", n * j + i + 1)
            a = bytearray(b[k] ^ t[k] for k in range(8))
            r[i] = bytearray(b[8:])

    return bytes(a) + b"".join(bytes(block) for block in r)
