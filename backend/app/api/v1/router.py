from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    assets,
    scans,
    vulnerabilities,
    alerts,
    dashboard,
    integrations,
    discovery,
    reports,
    users,
    health,
    websocket,
    setup,
)
# Free edition: attack-graph/ML risk scoring (graph), threat-intel
# correlation (threat_intel), and policy-driven automated remediation
# (policies) are paid-plan only — their route files are not included in
# this repo at all (not just disabled behind a flag).

api_router = APIRouter()

# First-time setup (no auth required)
api_router.include_router(setup.router, prefix="/setup", tags=["System Setup"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(scans.router, prefix="/scans", tags=["Scans"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["Discovery Engine"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(health.router, prefix="", tags=["Health & Metrics"])
