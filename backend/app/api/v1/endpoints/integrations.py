from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.core.vault import encrypt_config, mask_dict_secrets
from app.models.user import User
from app.models.integration import Integration, IntegrationStatus

router = APIRouter()


class IntegrationConfig(BaseModel):
    provider: str
    name: str
    config: dict
    is_enabled: bool = True


class IntegrationResponse(BaseModel):
    id: int
    provider: str
    name: str
    status: str
    is_enabled: bool
    last_sync: Optional[str]
    assets_synced: int
    config_masked: dict  # Only masked values returned

    class Config:
        from_attributes = True


@router.get("/")
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available and configured integrations. Secrets are masked."""
    # Get configured integrations from DB
    result = await db.execute(
        select(Integration).where(Integration.organization_id == current_user.organization_id)
    )
    configured = result.scalars().all()

    configured_list = []
    for integ in configured:
        configured_list.append({
            "id": integ.id,
            "provider": integ.provider,
            "name": integ.name,
            "status": integ.status.value if integ.status else "pending",
            "is_enabled": integ.is_enabled,
            "last_sync": integ.last_sync.isoformat() if integ.last_sync else None,
            "assets_synced": integ.assets_synced,
            "config_masked": integ.config_masked,
        })

    return {
        "available": [
            {
                "id": "aws",
                "name": "Amazon Web Services",
                "category": "cloud",
                "description": "Discover and monitor AWS resources",
                "icon": "aws",
                "config_fields": [
                    {"name": "access_key_id", "type": "string", "required": True},
                    {"name": "secret_access_key", "type": "password", "required": True},
                    {"name": "regions", "type": "multi_select", "options": ["us-east-1", "us-west-2", "eu-west-1"]},
                ],
            },
            {
                "id": "azure",
                "name": "Microsoft Azure",
                "category": "cloud",
                "description": "Discover and monitor Azure resources",
                "icon": "azure",
                "config_fields": [
                    {"name": "tenant_id", "type": "string", "required": True},
                    {"name": "client_id", "type": "string", "required": True},
                    {"name": "client_secret", "type": "password", "required": True},
                ],
            },
            {
                "id": "gcp",
                "name": "Google Cloud Platform",
                "category": "cloud",
                "description": "Discover and monitor GCP resources",
                "icon": "gcp",
                "config_fields": [
                    {"name": "project_id", "type": "string", "required": True},
                    {"name": "credentials_json", "type": "file", "required": True},
                ],
            },
            {
                "id": "github",
                "name": "GitHub",
                "category": "code",
                "description": "Discover repositories, secrets, and code exposure",
                "icon": "github",
                "config_fields": [
                    {"name": "token", "type": "password", "required": True},
                    {"name": "organization", "type": "string", "required": True},
                ],
            },
            {
                "id": "gitlab",
                "name": "GitLab",
                "category": "code",
                "description": "Discover repositories and CI/CD pipelines",
                "icon": "gitlab",
                "config_fields": [
                    {"name": "token", "type": "password", "required": True},
                    {"name": "url", "type": "string", "required": False},
                ],
            },
            {
                "id": "okta",
                "name": "Okta",
                "category": "identity",
                "description": "Discover users and identity configurations",
                "icon": "okta",
                "config_fields": [
                    {"name": "domain", "type": "string", "required": True},
                    {"name": "token", "type": "password", "required": True},
                ],
            },
            {
                "id": "crowdstrike",
                "name": "CrowdStrike",
                "category": "endpoint",
                "description": "Integrate with CrowdStrike Falcon for endpoint data",
                "icon": "crowdstrike",
                "config_fields": [
                    {"name": "api_key", "type": "password", "required": True},
                    {"name": "api_url", "type": "string", "required": True},
                ],
            },
            {
                "id": "jira",
                "name": "Jira",
                "category": "ticketing",
                "description": "Create and manage security tickets in Jira",
                "icon": "jira",
                "config_fields": [
                    {"name": "url", "type": "string", "required": True},
                    {"name": "email", "type": "string", "required": True},
                    {"name": "token", "type": "password", "required": True},
                    {"name": "project_key", "type": "string", "required": True},
                ],
            },
            {
                "id": "slack",
                "name": "Slack",
                "category": "notification",
                "description": "Send alerts and notifications to Slack channels",
                "icon": "slack",
                "config_fields": [
                    {"name": "webhook_url", "type": "string", "required": True},
                    {"name": "channel", "type": "string", "required": False},
                ],
            },
            {
                "id": "pagerduty",
                "name": "PagerDuty",
                "category": "notification",
                "description": "Create PagerDuty incidents for critical alerts",
                "icon": "pagerduty",
                "config_fields": [
                    {"name": "routing_key", "type": "password", "required": True},
                ],
            },
        ],
        "categories": ["cloud", "code", "identity", "endpoint", "ticketing", "notification", "siem"],
        "configured": configured_list,
    }


@router.post("/configure")
async def configure_integration(
    config: IntegrationConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin"])
    ),
):
    """Configure a new integration. API keys are encrypted before storage.
    NEVER returns the raw API key in the response."""
    # Check if integration already exists
    result = await db.execute(
        select(Integration).where(
            Integration.provider == config.provider,
            Integration.organization_id == current_user.organization_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.name = config.name
        existing.is_enabled = config.is_enabled
        existing.set_config(config.config)
    else:
        integration = Integration(
            name=config.name,
            provider=config.provider,
            status=IntegrationStatus.PENDING,
            is_enabled=config.is_enabled,
            organization_id=current_user.organization_id,
            created_by=current_user.id,
        )
        integration.set_config(config.config)
        db.add(integration)

    await db.commit()

    return {
        "message": f"Integration {config.provider} configured successfully",
        "status": "saved",
        "detail": "Credentials encrypted and stored securely. They will not be displayed again.",
    }


@router.get("/{provider}")
async def get_integration(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get integration details. Secrets are masked in response."""
    result = await db.execute(
        select(Integration).where(
            Integration.provider == provider,
            Integration.organization_id == current_user.organization_id,
        )
    )
    integ = result.scalar_one_or_none()

    if not integ:
        raise HTTPException(status_code=404, detail=f"Integration {provider} not configured")

    return {
        "id": integ.id,
        "provider": integ.provider,
        "name": integ.name,
        "status": integ.status.value if integ.status else "pending",
        "is_enabled": integ.is_enabled,
        "last_sync": integ.last_sync.isoformat() if integ.last_sync else None,
        "assets_synced": integ.assets_synced,
        "config_masked": integ.config_masked,
    }


@router.post("/{provider}/test")
async def test_integration(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin"])
    ),
):
    """Test an integration connection using decrypted credentials internally."""
    result = await db.execute(
        select(Integration).where(
            Integration.provider == provider,
            Integration.organization_id == current_user.organization_id,
        )
    )
    integ = result.scalar_one_or_none()

    if not integ:
        raise HTTPException(status_code=404, detail=f"Integration {provider} not configured")

    # Use decrypted config internally
    try:
        from app.services.integration_manager import IntegrationManager
        manager = IntegrationManager()
        decrypted = integ.config
        connected = await manager.test_connection(
            org_id=current_user.organization_id,
            provider=provider,
        )
    except Exception:
        connected = False

    return {"provider": provider, "status": "connected" if connected else "failed"}


@router.post("/{provider}/sync")
async def sync_integration(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Manually trigger a sync for an integration."""
    try:
        from app.services.tasks import sync_integration_task
        sync_integration_task.delay(
            org_id=current_user.organization_id,
            provider=provider,
        )
    except Exception:
        pass

    return {"message": f"Sync started for {provider}"}


@router.delete("/{provider}")
async def delete_integration(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin"])
    ),
):
    """Delete an integration and all stored credentials."""
    result = await db.execute(
        select(Integration).where(
            Integration.provider == provider,
            Integration.organization_id == current_user.organization_id,
        )
    )
    integ = result.scalar_one_or_none()

    if not integ:
        raise HTTPException(status_code=404, detail=f"Integration {provider} not found")

    await db.delete(integ)
    await db.commit()

    return {"message": f"Integration {provider} deleted. All credentials permanently removed."}
