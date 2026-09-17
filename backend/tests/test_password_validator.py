"""Tests for app.core.password_validator.

This module has no external dependencies (no DB/Redis), so it is covered
directly rather than through the API layer.
"""

from app.core.password_validator import (
    generate_secure_password,
    validate_password_strength,
)


def test_empty_password_is_rejected():
    ok, message = validate_password_strength("")
    assert ok is False
    assert "empty" in message.lower()


def test_too_few_digits_is_rejected():
    ok, _ = validate_password_strength("Abc12!xyz")
    assert ok is False


def test_all_same_digits_are_rejected():
    ok, message = validate_password_strength("Ab1111!x")
    assert ok is False
    assert "same" in message.lower()


def test_ascending_digits_are_rejected():
    ok, message = validate_password_strength("Ab1234!x")
    assert ok is False
    assert "ascending" in message.lower()


def test_descending_digits_are_rejected():
    ok, message = validate_password_strength("Ab4321!x")
    assert ok is False
    assert "descending" in message.lower()


def test_missing_special_character_is_rejected():
    ok, message = validate_password_strength("Ab13570x")
    assert ok is False
    assert "special" in message.lower()


def test_missing_uppercase_is_rejected():
    ok, message = validate_password_strength("ab1357!x")
    assert ok is False
    assert "uppercase" in message.lower()


def test_well_formed_password_is_accepted():
    # 4 non-consecutive, non-sequential digits, 1 special char, 1 uppercase.
    ok, message = validate_password_strength("Ab1!9573x")
    assert ok is True
    assert "meets requirements" in message.lower()


def test_generate_secure_password_length_and_character_classes():
    password = generate_secure_password()

    assert len(password) == 12
    assert any(c.isupper() for c in password)
    assert any(c.islower() for c in password)
    assert any(c.isdigit() for c in password)
    assert sum(c.isdigit() for c in password) == 5


def test_generate_secure_password_always_passes_validation():
    for _ in range(200):
        password = generate_secure_password()
        ok, message = validate_password_strength(password)
        assert ok is True, f"{password!r} failed validation: {message}"
