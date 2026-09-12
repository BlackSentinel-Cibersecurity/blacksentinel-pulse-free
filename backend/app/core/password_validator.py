import re
import secrets
import string


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength:
    - Minimum 4 numbers (non-consecutive, non-ascending, non-descending)
    - At least 1 special character
    - At least 1 uppercase letter
    - No limit on lowercase letters
    - No length limit
    """
    if not password:
        return False, "Password cannot be empty"

    digits = [int(c) for c in password if c.isdigit()]

    if len(digits) < 4:
        return False, f"Password must contain at least 4 numbers (found {len(digits)})"

    if len(digits) >= 2:
        is_consecutive_ascending = all(
            digits[i] == digits[i - 1] + 1 for i in range(1, len(digits))
        )
        is_consecutive_descending = all(
            digits[i] == digits[i - 1] - 1 for i in range(1, len(digits))
        )
        is_all_same = all(d == digits[0] for d in digits)

        if is_all_same:
            return False, "Numbers cannot all be the same"
        if is_consecutive_ascending:
            return False, "Numbers cannot be in ascending order (e.g., 1234)"
        if is_consecutive_descending:
            return False, "Numbers cannot be in descending order (e.g., 4321)"

    if len(digits) >= 2:
        has_consecutive = any(
            digits[i] == digits[i - 1] + 1 for i in range(1, len(digits))
        )
        if has_consecutive:
            return False, "Numbers cannot be consecutive (e.g., 12, 23, 34)"

    special_chars = set(string.punctuation)
    has_special = any(c in special_chars for c in password)
    if not has_special:
        return False, "Password must contain at least 1 special character (!@#$%^&*...)"

    has_upper = any(c.isupper() for c in password)
    if not has_upper:
        return False, "Password must contain at least 1 uppercase letter"

    return True, "Password meets requirements"


def generate_secure_password() -> str:
    """Generate a password that passes validation."""
    uppercase = random.sample(string.ascii_uppercase, 2)
    special = random.sample(list(string.punctuation), 2)

    while True:
        digits = random.sample(range(0, 10), 5)
        has_consecutive = any(
            digits[i] == digits[i - 1] + 1 for i in range(1, len(digits))
        )
        has_ascending = all(
            digits[i] > digits[i - 1] for i in range(1, len(digits))
        )
        has_descending = all(
            digits[i] < digits[i - 1] for i in range(1, len(digits))
        )
        if not has_consecutive and not has_ascending and not has_descending:
            break

    lowercase = random.sample(string.ascii_lowercase, 3)

    all_chars = uppercase + special + [str(d) for d in digits] + lowercase
    random.shuffle(all_chars)
    return "".join(all_chars)


import random
