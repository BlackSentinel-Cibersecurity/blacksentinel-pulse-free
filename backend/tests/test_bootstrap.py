"""Tests for app.core.bootstrap.ensure_secret_key (no DB/Redis needed)."""

import pytest

from app.core import bootstrap
from app.core.config import settings

COMPOSE_LITERAL = '$(python3 -c "import secrets; print(secrets.token_hex(32))")'
REAL_KEY = "9c1f4e7a2b8d5063f1a9c7e2b4d6f8a0c3e5f7a9b1d2e4f6a8c0e2f4a6b8d0e2"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "change-me-in-production",
        COMPOSE_LITERAL,
        "short",
        'generate_with: python3 -c "..."',
    ],
)
def test_public_or_weak_keys_are_replaced(monkeypatch, value):
    monkeypatch.setattr(settings, "SECRET_KEY", value)
    bootstrap.ensure_secret_key()
    assert settings.SECRET_KEY != value
    assert len(settings.SECRET_KEY) == 64


def test_a_real_key_is_kept(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", REAL_KEY)
    bootstrap.ensure_secret_key()
    assert settings.SECRET_KEY == REAL_KEY
