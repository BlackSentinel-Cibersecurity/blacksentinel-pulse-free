"""Initial schema - all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("plan", sa.String(50), server_default="professional"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("settings", postgresql.JSON(), server_default="{}"),
        sa.Column("notification_config", postgresql.JSON(), server_default="{}"),
        sa.Column("max_assets", sa.Integer(), server_default="10000"),
        sa.Column("max_users", sa.Integer(), server_default="10"),
        sa.Column("max_scans_per_day", sa.Integer(), server_default="100"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("subscription_id", sa.String(255), nullable=True),
        sa.Column("subscription_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), server_default="analyst"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_verified", sa.Boolean(), server_default="false"),
        sa.Column("mfa_enabled", sa.Boolean(), server_default="false"),
        sa.Column("mfa_secret", sa.String(32), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # Assets
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("risk_factors", postgresql.JSON(), server_default="{}"),
        sa.Column("criticality", sa.String(20), server_default="medium"),
        sa.Column("discovery_method", sa.String(100), nullable=True),
        sa.Column("discovery_source", sa.String(100), nullable=True),
        sa.Column("first_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_scan", sa.DateTime(), nullable=True),
        sa.Column("scan_count", sa.Integer(), server_default="0"),
        sa.Column("raw_data", postgresql.JSON(), server_default="{}"),
        sa.Column("tags", postgresql.JSON(), server_default="[]"),
        sa.Column("metadata", postgresql.JSON(), server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("protocol", sa.String(20), nullable=True),
        sa.Column("hostname", sa.String(500), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("asn", sa.Integer(), nullable=True),
        sa.Column("isp", sa.String(255), nullable=True),
        sa.Column("whois_data", postgresql.JSON(), server_default="{}"),
        sa.Column("registrar", sa.String(255), nullable=True),
        sa.Column("registrant_org", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("renewal_cost", sa.Float(), nullable=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_assets_uuid", "assets", ["uuid"])
    op.create_index("ix_assets_name", "assets", ["name"])
    op.create_index("ix_assets_asset_type", "assets", ["asset_type"])
    op.create_index("ix_assets_status", "assets", ["status"])
    op.create_index("ix_assets_risk_score", "assets", ["risk_score"])

    # Vulnerabilities
    op.create_table(
        "vulnerabilities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("cvss_vector", sa.String(200), nullable=True),
        sa.Column("cwe_id", sa.String(20), nullable=True),
        sa.Column("status", sa.String(50), server_default="open"),
        sa.Column("false_positive", sa.Boolean(), server_default="false"),
        sa.Column("affected_component", sa.String(255), nullable=True),
        sa.Column("affected_version", sa.String(100), nullable=True),
        sa.Column("fixed_version", sa.String(100), nullable=True),
        sa.Column("exploit_available", sa.Boolean(), server_default="false"),
        sa.Column("exploit_in_wild", sa.Boolean(), server_default="false"),
        sa.Column("patch_available", sa.Boolean(), server_default="false"),
        sa.Column("evidence", postgresql.JSON(), server_default="{}"),
        sa.Column("proof_of_concept", sa.Text(), nullable=True),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("references", postgresql.JSON(), server_default="[]"),
        sa.Column("discovery_method", sa.String(100), nullable=True),
        sa.Column("scanner", sa.String(100), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("risk_factors", postgresql.JSON(), server_default="{}"),
        sa.Column("exploitability_score", sa.Float(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_verified", sa.DateTime(), nullable=True),
        sa.Column("remediated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vulnerabilities_external_id", "vulnerabilities", ["external_id"]
    )

    # Scans
    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("scan_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("config", postgresql.JSON(), server_default="{}"),
        sa.Column("targets", postgresql.JSON(), server_default="[]"),
        sa.Column("options", postgresql.JSON(), server_default="{}"),
        sa.Column("progress", sa.Integer(), server_default="0"),
        sa.Column("current_step", sa.String(255), nullable=True),
        sa.Column("total_steps", sa.Integer(), server_default="0"),
        sa.Column("completed_steps", sa.Integer(), server_default="0"),
        sa.Column("assets_found", sa.Integer(), server_default="0"),
        sa.Column("vulnerabilities_found", sa.Integer(), server_default="0"),
        sa.Column("critical_findings", sa.Integer(), server_default="0"),
        sa.Column("high_findings", sa.Integer(), server_default="0"),
        sa.Column("medium_findings", sa.Integer(), server_default="0"),
        sa.Column("low_findings", sa.Integer(), server_default="0"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("triggered_by", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSON(), server_default="{}"),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("scan_config_version", sa.String(20), nullable=True),
        sa.Column("engine_version", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id"),
    )

    # Alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alert_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(50), server_default="open"),
        sa.Column("alert_type", sa.String(100), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("rule_id", sa.String(100), nullable=True),
        sa.Column("detection_method", sa.String(100), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("related_alerts", postgresql.JSON(), server_default="[]"),
        sa.Column("incident_id", sa.String(36), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("ai_recommendation", sa.Text(), nullable=True),
        sa.Column("auto_remediation_available", sa.Boolean(), server_default="false"),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column(
            "vulnerability_id",
            sa.Integer(),
            sa.ForeignKey("vulnerabilities.id"),
            nullable=True,
        ),
        sa.Column("business_impact", sa.String(50), nullable=True),
        sa.Column("blast_radius", sa.Integer(), server_default="0"),
        sa.Column("exploitability", sa.Float(), nullable=True),
        sa.Column("evidence", postgresql.JSON(), server_default="[]"),
        sa.Column("raw_data", postgresql.JSON(), server_default="{}"),
        sa.Column("notified", sa.Boolean(), server_default="false"),
        sa.Column("notification_channels", postgresql.JSON(), server_default="[]"),
        sa.Column(
            "acknowledged_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "resolved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("auto_resolved", sa.Boolean(), server_default="false"),
        sa.Column("sla_deadline", sa.DateTime(), nullable=True),
        sa.Column("sla_breached", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alert_id"),
    )

    # Threat Intelligence
    op.create_table(
        "threat_intelligence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("threat_type", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.0"),
        sa.Column("severity", sa.String(20), server_default="medium"),
        sa.Column("indicators", postgresql.JSON(), server_default="[]"),
        sa.Column("indicator_type", sa.String(50), nullable=True),
        sa.Column("indicator_value", sa.String(500), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ttps", postgresql.JSON(), server_default="[]"),
        sa.Column("tags", postgresql.JSON(), server_default="[]"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_reliability", sa.Float(), nullable=True),
        sa.Column("raw_data", postgresql.JSON(), server_default="{}"),
        sa.Column("first_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_threat_intelligence_indicator_value",
        "threat_intelligence",
        ["indicator_value"],
    )

    # Certificates
    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("fingerprint_sha256", sa.String(64), nullable=True),
        sa.Column("fingerprint_sha1", sa.String(40), nullable=True),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("issuer", sa.String(500), nullable=True),
        sa.Column("subject_alt_names", postgresql.JSON(), server_default="[]"),
        sa.Column("common_name", sa.String(255), nullable=True),
        sa.Column("not_before", sa.DateTime(), nullable=True),
        sa.Column("not_after", sa.DateTime(), nullable=True),
        sa.Column("is_expired", sa.Boolean(), server_default="false"),
        sa.Column("is_valid", sa.Boolean(), server_default="true"),
        sa.Column("days_until_expiry", sa.Integer(), nullable=True),
        sa.Column("is_self_signed", sa.Boolean(), server_default="false"),
        sa.Column("is_wildcard", sa.Boolean(), server_default="false"),
        sa.Column("is_ev", sa.Boolean(), server_default="false"),
        sa.Column("is_ca", sa.Boolean(), server_default="false"),
        sa.Column("key_size", sa.Integer(), nullable=True),
        sa.Column("signature_algorithm", sa.String(50), nullable=True),
        sa.Column("chain_depth", sa.Integer(), server_default="0"),
        sa.Column(
            "parent_certificate_id",
            sa.Integer(),
            sa.ForeignKey("certificates.id"),
            nullable=True,
        ),
        sa.Column("ct_log", postgresql.JSON(), server_default="[]"),
        sa.Column("first_seen_ct", sa.DateTime(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("raw_cert", sa.Text(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint_sha256"),
    )

    # DNS Records
    op.create_table(
        "dns_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("record_type", sa.String(10), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("ttl", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("is_dnssec", sa.Boolean(), server_default="false"),
        sa.Column("dnssec_algorithm", sa.String(20), nullable=True),
        sa.Column("nameserver", sa.String(255), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_verified", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # API Endpoints
    op.create_table(
        "api_endpoints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(1000), nullable=False),
        sa.Column("full_url", sa.String(2000), nullable=True),
        sa.Column("api_version", sa.String(20), nullable=True),
        sa.Column("api_type", sa.String(50), nullable=True),
        sa.Column("requires_auth", sa.Boolean(), server_default="false"),
        sa.Column("auth_type", sa.String(50), nullable=True),
        sa.Column("response_format", sa.String(20), nullable=True),
        sa.Column("status_codes", postgresql.JSON(), server_default="[]"),
        sa.Column("has_cors", sa.Boolean(), server_default="false"),
        sa.Column("cors_origins", postgresql.JSON(), server_default="[]"),
        sa.Column("rate_limited", sa.Boolean(), server_default="false"),
        sa.Column("discovery_method", sa.String(100), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default="true"),
        sa.Column("is_deprecated", sa.Boolean(), server_default="false"),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_verified", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Cloud Resources
    op.create_table(
        "cloud_resources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("arn", sa.String(500), nullable=True),
        sa.Column("region", sa.String(50), nullable=True),
        sa.Column("config", postgresql.JSON(), server_default="{}"),
        sa.Column("tags", postgresql.JSON(), server_default="{}"),
        sa.Column("public_ip", sa.String(45), nullable=True),
        sa.Column("private_ip", sa.String(45), nullable=True),
        sa.Column("vpc_id", sa.String(255), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default="false"),
        sa.Column("is_internet_facing", sa.Boolean(), server_default="false"),
        sa.Column("monthly_cost", sa.Float(), nullable=True),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("misconfigurations", postgresql.JSON(), server_default="[]"),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_synced", sa.DateTime(), nullable=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Credential Exposures
    op.create_table(
        "credential_exposures",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("credential_type", sa.String(50), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("service", sa.String(255), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("exposure_type", sa.String(50), nullable=True),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_valid", sa.Boolean(), server_default="false"),
        sa.Column("last_validated", sa.DateTime(), nullable=True),
        sa.Column("evidence_hash", sa.String(255), nullable=True),
        sa.Column("redacted_preview", sa.String(255), nullable=True),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Asset Relationships
    op.create_table(
        "asset_relationships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "source_asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False
        ),
        sa.Column(
            "target_asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False
        ),
        sa.Column("relationship_type", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0"),
        sa.Column("metadata", postgresql.JSON(), server_default="{}"),
        sa.Column("is_bidirectional", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_verified", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Policies
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("policy_type", sa.String(50), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default="true"),
        sa.Column("conditions", postgresql.JSON(), nullable=False),
        sa.Column("actions", postgresql.JSON(), nullable=False),
        sa.Column("scope", postgresql.JSON(), server_default="{}"),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("last_triggered", sa.DateTime(), nullable=True),
        sa.Column("trigger_count", sa.Integer(), server_default="0"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Integrations
    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("is_enabled", sa.Boolean(), server_default="true"),
        sa.Column("config", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("last_sync", sa.DateTime(), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("assets_synced", sa.Integer(), server_default="0"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_integrations_provider", "integrations", ["provider"])

    # Incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("incident_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("status", sa.String(50), server_default="detected"),
        sa.Column("incident_type", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("ttps", postgresql.JSON(), server_default="[]"),
        sa.Column("affected_assets", postgresql.JSON(), server_default="[]"),
        sa.Column("affected_users", sa.Integer(), server_default="0"),
        sa.Column("data_classification", sa.String(50), nullable=True),
        sa.Column("estimated_impact", sa.String(50), nullable=True),
        sa.Column(
            "assigned_to", sa.Integer(), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("response_team", postgresql.JSON(), server_default="[]"),
        sa.Column("timeline", postgresql.JSON(), server_default="[]"),
        sa.Column("actions_taken", postgresql.JSON(), server_default="[]"),
        sa.Column("evidence", postgresql.JSON(), server_default="[]"),
        sa.Column("iocs", postgresql.JSON(), server_default="[]"),
        sa.Column("raw_data", postgresql.JSON(), server_default="{}"),
        sa.Column("time_to_detect", sa.Integer(), nullable=True),
        sa.Column("time_to_contain", sa.Integer(), nullable=True),
        sa.Column("time_to_recover", sa.Integer(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("triaged_at", sa.DateTime(), nullable=True),
        sa.Column("contained_at", sa.DateTime(), nullable=True),
        sa.Column("eradicated_at", sa.DateTime(), nullable=True),
        sa.Column("recovered_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_id"),
    )

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("permissions", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )

    # Scan Assets (association table)
    op.create_table(
        "scan_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.Integer(), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("is_new", sa.Boolean(), server_default="true"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Scan Results
    op.create_table(
        "scan_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.Integer(), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("result_type", sa.String(100), nullable=False),
        sa.Column("data", postgresql.JSON(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Integer(), server_default="100"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("scan_results")
    op.drop_table("scan_assets")
    op.drop_table("api_keys")
    op.drop_table("incidents")
    op.drop_table("integrations")
    op.drop_table("policies")
    op.drop_table("asset_relationships")
    op.drop_table("credential_exposures")
    op.drop_table("cloud_resources")
    op.drop_table("api_endpoints")
    op.drop_table("dns_records")
    op.drop_table("certificates")
    op.drop_table("threat_intelligence")
    op.drop_table("alerts")
    op.drop_table("scans")
    op.drop_table("vulnerabilities")
    op.drop_table("assets")
    op.drop_table("users")
    op.drop_table("organizations")
