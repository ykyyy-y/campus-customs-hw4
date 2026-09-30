"""Password hashing for Campus Customs accounts.

Passwords are never stored, logged, or returned by the API. What goes in the `users`
table is a one-way PBKDF2-HMAC-SHA256 digest:

    pbkdf2_sha256$<16-hex-char salt>$<64-hex-char digest>

Three properties matter here:

1. **One-way.** PBKDF2 cannot be reversed. Someone who steals the database file gets
   digests, not passwords.
2. **Salted per user.** Every account gets its own random salt, so two people who pick
   the same password still get different digests, and a precomputed rainbow table is
   useless.
3. **Deliberately slow.** 120,000 iterations makes each guess expensive, which is what
   turns a stolen digest into an impractical brute-force target.

The iteration count matches the seed data (verified against the provided test user), so
seeded accounts and accounts created through the website verify through this same code.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
SALT_BYTES = 8  # 8 bytes -> 16 hex characters, matching the seeded rows
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str, salt: str | None = None) -> str:
    """Return the storable `pbkdf2_sha256$salt$digest` string for a plaintext password."""
    salt = salt or secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    ).hex()
    return f"{ALGORITHM}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Check a plaintext password against a stored hash.

    Uses `hmac.compare_digest` rather than `==` so the comparison takes the same time
    whichever byte differs first, and never leaks how much of a guess was correct.
    """
    try:
        algorithm, salt, expected = stored.split("$")
    except (AttributeError, ValueError):
        return False
    if algorithm != ALGORITHM:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS
    ).hex()
    return hmac.compare_digest(candidate, expected)


# A throwaway digest to verify against when the email does not exist, so a failed login
# costs the same time either way and cannot be used to probe which emails are registered.
DUMMY_HASH = hash_password("not-a-real-password")


def password_problem(password: str) -> str | None:
    """Return a complaint about a new password, or None if it is acceptable."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Please choose a password of at least {MIN_PASSWORD_LENGTH} characters."
    return None


def normalize_email(email: str) -> str:
    """Emails are matched case-insensitively, so store and compare them lowercased."""
    return email.strip().lower()
