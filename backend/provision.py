#!/usr/bin/env python3
"""
BlackSentinel Pulse - Multi-Tenant Organization Provisioning Tool

Usage:
    python provision.py create --name "Acme Corp" --slug acme --plan enterprise
    python provision.py list
    python provision.py deactivate --slug acme
    python provision.py export --slug acme --format json
"""

import asyncio
import argparse
import json
import secrets
import sys
from datetime import datetime

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password, generate_api_key
from app.models.user import User, UserRole
from app.models.organization import Organization


async def create_org(name: str, slug: str, plan: str = "professional",
                     admin_email: str = None, admin_password: str = None):
    """Create a new organization with admin user."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check if org exists
        existing = await db.execute(select(Organization).where(Organization.slug == slug))
        if existing.scalar_one_or_none():
            print(f"Organization '{slug}' already exists!")
            await engine.dispose()
            return

        # Limits per plan
        limits = {
            "free": {"max_assets": 100, "max_users": 3, "max_scans": 10},
            "professional": {"max_assets": 10000, "max_users": 10, "max_scans": 100},
            "enterprise": {"max_assets": 100000, "max_users": 100, "max_scans": 1000},
        }
        l = limits.get(plan, limits["professional"])

        # Create organization
        org = Organization(
            name=name,
            slug=slug,
            plan=plan,
            max_assets=l["max_assets"],
            max_users=l["max_users"],
            max_scans_per_day=l["max_scans"],
        )
        db.add(org)
        await db.flush()

        # Create admin user
        password = admin_password or f"change-me-{secrets.token_hex(4)}"
        admin = User(
            email=admin_email or f"admin@{slug}.com",
            username=f"admin-{slug}",
            hashed_password=hash_password(password),
            full_name=f"Admin - {name}",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            organization_id=org.id,
        )
        db.add(admin)
        await db.commit()

        print(f"\n{'='*60}")
        print(f"  Organization Created: {name}")
        print(f"{'='*60}")
        print(f"  Slug:       {slug}")
        print(f"  Plan:       {plan}")
        print(f"  Max Assets: {l['max_assets']:,}")
        print(f"  Max Users:  {l['max_users']}")
        print(f"  Max Scans:  {l['max_scans']}/day")
        print(f"\n  Admin User:")
        print(f"    Email:    {admin.email}")
        print(f"    Username: {admin.username}")
        print(f"    Password: {password}")
        print(f"{'='*60}\n")

    await engine.dispose()


async def list_orgs():
    """List all organizations."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        result = await db.execute(select(Organization).order_by(Organization.created_at.desc()))
        orgs = result.scalars().all()

        if not orgs:
            print("No organizations found.")
            await engine.dispose()
            return

        print(f"\n{'Name':<30} {'Slug':<20} {'Plan':<15} {'Assets':<10} {'Status'}")
        print("-" * 95)
        for org in orgs:
            status = "Active" if org.is_active else "Inactive"
            print(f"{org.name:<30} {org.slug:<20} {org.plan:<15} {org.max_assets:<10} {status}")
        print()

    await engine.dispose()


async def deactivate_org(slug: str):
    """Deactivate an organization."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        org = result.scalar_one_or_none()

        if not org:
            print(f"Organization '{slug}' not found!")
            await engine.dispose()
            return

        org.is_active = False
        await db.commit()
        print(f"Organization '{org.name}' deactivated.")

    await engine.dispose()


async def export_org(slug: str, format: str = "json"):
    """Export organization data."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        org = result.scalar_one_or_none()

        if not org:
            print(f"Organization '{slug}' not found!")
            await engine.dispose()
            return

        # Get users
        users_result = await db.execute(
            select(User).where(User.organization_id == org.id)
        )
        users = users_result.scalars().all()

        data = {
            "organization": {
                "name": org.name,
                "slug": org.slug,
                "plan": org.plan,
                "created_at": org.created_at.isoformat() if org.created_at else None,
            },
            "users": [
                {
                    "email": u.email,
                    "username": u.username,
                    "role": u.role.value if u.role else "analyst",
                    "is_active": u.is_active,
                }
                for u in users
            ],
            "exported_at": datetime.utcnow().isoformat(),
        }

        print(json.dumps(data, indent=2))

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="BlackSentinel Pulse Provisioning")
    subparsers = parser.add_subparsers(dest="command")

    # Create
    create_parser = subparsers.add_parser("create", help="Create organization")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--slug", required=True)
    create_parser.add_argument("--plan", default="professional", choices=["free", "professional", "enterprise"])
    create_parser.add_argument("--admin-email")
    create_parser.add_argument("--admin-password")

    # List
    subparsers.add_parser("list", help="List organizations")

    # Deactivate
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate organization")
    deactivate_parser.add_argument("--slug", required=True)

    # Export
    export_parser = subparsers.add_parser("export", help="Export organization data")
    export_parser.add_argument("--slug", required=True)
    export_parser.add_argument("--format", default="json")

    args = parser.parse_args()

    if args.command == "create":
        asyncio.run(create_org(args.name, args.slug, args.plan, args.admin_email, args.admin_password))
    elif args.command == "list":
        asyncio.run(list_orgs())
    elif args.command == "deactivate":
        asyncio.run(deactivate_org(args.slug))
    elif args.command == "export":
        asyncio.run(export_org(args.slug, args.format))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
