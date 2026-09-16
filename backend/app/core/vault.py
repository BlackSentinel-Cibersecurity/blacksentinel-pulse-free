"""
BlackSentinel Pulse - Military-Grade Credential Security Module

All API keys, tokens, and secrets are encrypted at rest using Fernet (AES-128-CBC).
Keys are NEVER returned in API responses - only masked versions (e.g., "ak_****xyz").
"""
import base64
import secrets
import os
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


_KEY_FILE = Path.home() / ".blacksentinel" / "vault.key"
_fernet: Fernet | None = None


def _derive_key(passphrase: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase))


def init_vault(passphrase: str | None = None) -> Fernet:
    """Initialize or load the encryption vault. Called once at startup."""
    global _fernet
    if _fernet is not None:
        return _fernet

    if passphrase is None:
        passphrase = os.environ.get("VAULT_PASSPHRASE", "")

    if _KEY_FILE.exists():
        raw = _KEY_FILE.read_bytes()
        salt = raw[:16]
        key = raw[16:]
        _fernet = Fernet(key)
    else:
        salt = secrets.token_bytes(16)
        key = _derive_key(passphrase.encode(), salt)
        _fernet = Fernet(key)
        _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _KEY_FILE.write_bytes(salt + key)
        os.chmod(_KEY_FILE, 0o600)

    return _fernet


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret value for storage. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""
    f = init_vault()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a stored secret. Returns plaintext."""
    if not ciphertext:
        return ""
    f = init_vault()
    return f.decrypt(ciphertext.encode()).decode()


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """Mask a secret for display. Shows first 2 and last `visible_chars` chars."""
    if not value or len(value) <= visible_chars + 2:
        return "****"
    return (
        f"{value[:2]}{'*' * (len(value) - visible_chars - 2)}{value[-visible_chars:]}"
    )


def mask_dict_secrets(data: dict, secret_keys: list[str] | None = None) -> dict:
    """Return a copy of the dict with all secret values masked."""
    if secret_keys is None:
        secret_keys = [
            "api_key",
            "secret_key",
            "access_key",
            "token",
            "password",
            "secret",
            "private_key",
            "client_secret",
            "api_secret",
            "access_token",
            "refresh_token",
            "secret_access_key",
        ]
    masked = {}
    for k, v in data.items():
        if isinstance(v, str) and any(sk in k.lower() for sk in secret_keys):
            masked[k] = mask_secret(v)
        elif isinstance(v, dict):
            masked[k] = mask_dict_secrets(v, secret_keys)
        else:
            masked[k] = v
    return masked


def encrypt_config(config: dict) -> dict:
    """Encrypt all secret values in a config dict before storing."""
    secret_keys = [
        "api_key",
        "secret_key",
        "access_key",
        "token",
        "password",
        "secret",
        "private_key",
        "client_secret",
        "api_secret",
        "access_token",
        "refresh_token",
        "secret_access_key",
        "aws_secret_access_key",
        "azure_client_secret",
        "github_token",
    ]
    encrypted = {}
    for k, v in config.items():
        if isinstance(v, str) and any(sk in k.lower() for sk in secret_keys) and v:
            encrypted[k] = encrypt_secret(v)
        elif isinstance(v, dict):
            encrypted[k] = encrypt_config(v)
        else:
            encrypted[k] = v
    return encrypted


def decrypt_config(config: dict) -> dict:
    """Decrypt all secret values in a config dict for use."""
    secret_keys = [
        "api_key",
        "secret_key",
        "access_key",
        "token",
        "password",
        "secret",
        "private_key",
        "client_secret",
        "api_secret",
        "access_token",
        "refresh_token",
        "secret_access_key",
        "aws_secret_access_key",
        "azure_client_secret",
        "github_token",
    ]
    decrypted = {}
    for k, v in config.items():
        if isinstance(v, str) and any(sk in k.lower() for sk in secret_keys) and v:
            try:
                decrypted[k] = decrypt_secret(v)
            except Exception:
                decrypted[k] = v
        elif isinstance(v, dict):
            decrypted[k] = decrypt_config(v)
        else:
            decrypted[k] = v
    return decrypted
