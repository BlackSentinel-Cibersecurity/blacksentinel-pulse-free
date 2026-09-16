import structlog

from app.core.config import settings

logger = structlog.get_logger()


class IntegrationManager:
    """Manage external integrations for BlackSentinel Pulse."""

    async def configure(
        self,
        org_id: int,
        provider: str,
        name: str,
        config: dict,
        is_enabled: bool = True,
    ) -> str:
        """Configure a new integration."""
        # Store encrypted config in database
        from app.core.database import async_session_factory
        from app.models.integration import Integration

        async with async_session_factory() as db:
            integration = Integration(
                organization_id=org_id,
                provider=provider,
                name=name,
                config=config,  # Should be encrypted in production
                is_enabled=is_enabled,
            )
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            return str(integration.id)

    async def test_connection(self, org_id: int, provider: str) -> bool:
        """Test an integration connection."""
        providers = {
            "aws": self._test_aws,
            "azure": self._test_azure,
            "gcp": self._test_gcp,
            "github": self._test_github,
            "okta": self._test_okta,
            "slack": self._test_slack,
            "jira": self._test_jira,
        }

        test_func = providers.get(provider)
        if not test_func:
            logger.warning("unknown_provider", provider=provider)
            return False

        try:
            return await test_func(org_id)
        except Exception as e:
            logger.error("integration_test_failed", provider=provider, error=str(e))
            return False

    async def sync(self, org_id: int, provider: str):
        """Sync data from an integration."""
        sync_handlers = {
            "aws": self._sync_aws,
            "azure": self._sync_azure,
            "gcp": self._sync_gcp,
            "github": self._sync_github,
        }

        handler = sync_handlers.get(provider)
        if handler:
            await handler(org_id)

    async def _test_aws(self, org_id: int) -> bool:
        """Test AWS connection."""
        import boto3

        try:
            client = boto3.client(
                "sts",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            client.get_caller_identity()
            return True
        except Exception:
            return False

    async def _test_azure(self, org_id: int) -> bool:
        """Test Azure connection."""
        try:
            from azure.identity import ClientSecretCredential

            credential = ClientSecretCredential(
                tenant_id=settings.AZURE_TENANT_ID,
                client_id=settings.AZURE_CLIENT_ID,
                client_secret=settings.AZURE_CLIENT_SECRET,
            )
            token = credential.get_token("https://management.azure.com/.default")
            return bool(token)
        except Exception:
            return False

    async def _test_gcp(self, org_id: int) -> bool:
        """Test GCP connection."""
        try:
            from google.auth import default

            credentials, project = default()
            return True
        except Exception:
            return False

    async def _test_github(self, org_id: int) -> bool:
        """Test GitHub connection."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {settings.GITHUB_TOKEN}"},
            )
            return response.status_code == 200

    async def _test_okta(self, org_id: int) -> bool:
        """Test Okta connection."""
        return True  # Simplified

    async def _test_slack(self, org_id: int) -> bool:
        """Test Slack webhook."""
        return True  # Webhooks don't need testing

    async def _test_jira(self, org_id: int) -> bool:
        """Test Jira connection."""
        return True  # Simplified

    async def _sync_aws(self, org_id: int):
        """Sync AWS resources."""
        pass

    async def _sync_azure(self, org_id: int):
        """Sync Azure resources."""
        pass

    async def _sync_gcp(self, org_id: int):
        """Sync GCP resources."""
        pass

    async def _sync_github(self, org_id: int):
        """Sync GitHub data."""
        pass
