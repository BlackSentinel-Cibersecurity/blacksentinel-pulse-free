"""First-start setup: secrets and the first administrator.

Under docker compose nothing ran seed.py, so Pulse started with no users and
nobody could sign in. ``ensure_first_admin`` creates one super admin (and the
default organization) only when the users table is empty. Its password is
ADMIN_PASSWORD (12+ characters) or a random one printed once in the log, and
the first sign-in must change it. This replaces seed.py's published
admin123 / analyst123 / viewer123.
"""

import os
import re
import secrets

import structlog
from sqlalchemy import func, select

from app.core.config import settings

logger = structlog.get_logger()

_PLACEHOLDER = re.compile(
    r"change-me|change_me|generate_with|\$\(|your[-_]|example|placeholder", re.I
)


def ensure_secret_key() -> None:
    """Never sign tokens with a public SECRET_KEY.

    SECURITY FIX: docker-compose.yml defaulted SECRET_KEY to the text
    ``$(python3 -c ...)``. Compose does not run commands, so that literal,
    public string became the signing key and anyone could forge tokens. Any
    missing, short or placeholder key is now replaced with a random one for
    this process (sessions end on restart; run scripts/init-env.sh to keep one).
    """
    key = (settings.SECRET_KEY or "").strip()
    if len(key) >= 32 and not _PLACEHOLDER.search(key):
        return
    generated = secrets.token_hex(32)
    os.environ["SECRET_KEY"] = generated
    settings.SECRET_KEY = generated
    logger.warning(
        "SECRET_KEY was missing or a placeholder; using a random key for this run. "
        "Run scripts/init-env.sh to keep one in .env."
    )


async def ensure_first_admin() -> None:
    from app.core.database import async_session_factory
    from app.core.security import hash_password
    from app.models.organization import Organization
    from app.models.user import User, UserRole

    async with async_session_factory() as db:
        count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
        if count:
            return

        org = (
            await db.execute(select(Organization).where(Organization.slug == "default"))
        ).scalar_one_or_none()
        if org is None:
            org = Organization(
                name="Default Organization",
                slug="default",
                description="Default organization for BlackSentinel Pulse",
                plan="enterprise",
                max_assets=100000,
                max_users=100,
                max_scans_per_day=1000,
            )
            db.add(org)
            await db.flush()

        configured = (os.environ.get("ADMIN_PASSWORD") or "").strip()
        from_env = len(configured) >= 12
        password = configured if from_env else secrets.token_urlsafe(12)
        email = (os.environ.get("ADMIN_EMAIL") or "admin@blacksentinel.local").strip()

        db.add(
            User(
                email=email,
                username="admin",
                hashed_password=hash_password(password),
                full_name="Administrator",
                role=UserRole.SUPER_ADMIN,
                is_active=True,
                is_verified=True,
                force_password_change=True,
                organization_id=org.id,
            )
        )
        await db.commit()

    if from_env:
        logger.info(
            "First admin created (password from ADMIN_PASSWORD)", username="admin"
        )
    else:
        logger.warning(
            f"First admin created: admin / {password}  <- shown only this once; you must change it at first sign-in."
        )
