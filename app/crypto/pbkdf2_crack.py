"""PBKDF2 PIN brute force for iOS restrictions and Screen Time passcodes."""
import hashlib
import time
from typing import Callable


def crack_pin(
    target_hash: bytes,
    salt: bytes,
    iterations: int = 1000,
    hash_algo: str = "sha1",
    dk_len: int = 20,
    max_digits: int = 4,
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[str | None, float]:
    """
    Brute-force a numeric PIN by iterating all possible combinations.

    Args:
        target_hash: The expected PBKDF2-derived key to match against.
        salt: Salt bytes used in PBKDF2.
        iterations: PBKDF2 iteration count (typically 1000 for iOS).
        hash_algo: Hash algorithm ('sha1' or 'sha256').
        dk_len: Derived key length in bytes.
        max_digits: PIN length (4 for restrictions, 4 or 6 for Screen Time).
        progress_callback: Optional callback(current, total) for progress updates.

    Returns:
        Tuple of (found_pin or None, elapsed_seconds).
    """
    max_pin = 10**max_digits
    start_time = time.time()

    for pin_int in range(max_pin):
        pin_str = str(pin_int).zfill(max_digits)
        derived = hashlib.pbkdf2_hmac(
            hash_algo, pin_str.encode("utf-8"), salt, iterations, dklen=dk_len
        )
        if derived == target_hash:
            elapsed = time.time() - start_time
            if progress_callback:
                progress_callback(max_pin, max_pin)
            return pin_str, elapsed

        if progress_callback and pin_int % 200 == 0:
            progress_callback(pin_int, max_pin)

    elapsed = time.time() - start_time
    return None, elapsed


def crack_pin_multi(
    target_hash: bytes,
    salt: bytes,
    iterations: int = 1000,
    hash_algo: str = "sha1",
    dk_len: int = 20,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> tuple[str | None, int, float]:
    """
    Try 4-digit first, then 6-digit if not found.

    Returns:
        Tuple of (found_pin or None, digit_count, elapsed_seconds).
    """
    # Try 4-digit first (most common)
    def cb4(current, total):
        if progress_callback:
            progress_callback(current, total, "4-digit")

    pin, elapsed = crack_pin(
        target_hash, salt, iterations, hash_algo, dk_len, 4, cb4
    )
    if pin:
        return pin, 4, elapsed

    # Try 6-digit
    def cb6(current, total):
        if progress_callback:
            progress_callback(current, total, "6-digit")

    pin, elapsed6 = crack_pin(
        target_hash, salt, iterations, hash_algo, dk_len, 6, cb6
    )
    return pin, 6, elapsed + elapsed6
