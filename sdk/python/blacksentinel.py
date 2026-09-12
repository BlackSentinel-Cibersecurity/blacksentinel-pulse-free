"""
BlackSentinel Pulse - Python SDK

Usage:
    from blacksentinel import PulseClient

    client = PulseClient(base_url="http://localhost:8000", api_key="ps_xxx")
    # or login with username/password
    client = PulseClient(base_url="http://localhost:8000")
    client.login("admin", "admin123")

    # Get assets
    assets = client.assets.list(page=1, page_size=10)

    # Get dashboard
    summary = client.dashboard.summary()

    # Start a scan
    scan = client.scans.create(name="My Scan", scan_type="full_discovery")
"""
import httpx
from dataclasses import dataclass
from typing import Optional


class PulseAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")


@dataclass
class AssetsAPI:
    _client: "PulseClient"

    def list(self, page: int = 1, page_size: int = 50, **filters):
        params = {"page": page, "page_size": page_size, **filters}
        return self._client._get("/api/v1/assets/", params=params)

    def get(self, asset_id: int):
        return self._client._get(f"/api/v1/assets/{asset_id}")

    def create(self, name: str, asset_type: str, **kwargs):
        return self._client._post("/api/v1/assets/", json={"name": name, "asset_type": asset_type, **kwargs})

    def delete(self, asset_id: int):
        return self._client._delete(f"/api/v1/assets/{asset_id}")


@dataclass
class ScansAPI:
    _client: "PulseClient"

    def list(self, page: int = 1, page_size: int = 20):
        return self._client._get("/api/v1/scans/", params={"page": page, "page_size": page_size})

    def get(self, scan_id: int):
        return self._client._get(f"/api/v1/scans/{scan_id}")

    def create(self, name: str, scan_type: str, targets: list = None, **kwargs):
        return self._client._post("/api/v1/scans/", json={"name": name, "scan_type": scan_type, "targets": targets or [], **kwargs})

    def cancel(self, scan_id: int):
        return self._client._post(f"/api/v1/scans/{scan_id}/cancel")


@dataclass
class VulnerabilitiesAPI:
    _client: "PulseClient"

    def list(self, page: int = 1, page_size: int = 50, **filters):
        params = {"page": page, "page_size": page_size, **filters}
        return self._client._get("/api/v1/vulnerabilities/", params=params)

    def get(self, vuln_id: int):
        return self._client._get(f"/api/v1/vulnerabilities/{vuln_id}")


@dataclass
class AlertsAPI:
    _client: "PulseClient"

    def list(self, page: int = 1, page_size: int = 50, **filters):
        params = {"page": page, "page_size": page_size, **filters}
        return self._client._get("/api/v1/alerts/", params=params)

    def acknowledge(self, alert_id: int):
        return self._client._post(f"/api/v1/alerts/{alert_id}/acknowledge")

    def resolve(self, alert_id: int, notes: str = ""):
        return self._client._post(f"/api/v1/alerts/{alert_id}/resolve", json={"resolution_notes": notes})


@dataclass
class DashboardAPI:
    _client: "PulseClient"

    def summary(self):
        return self._client._get("/api/v1/dashboard/summary")

    def risk_overview(self):
        return self._client._get("/api/v1/dashboard/risk-overview")


@dataclass
class DiscoveryAPI:
    _client: "PulseClient"

    def start(self, discovery_type: str, targets: list, **kwargs):
        return self._client._post("/api/v1/discovery/start", json={"discovery_type": discovery_type, "targets": targets, **kwargs})

    def status(self):
        return self._client._get("/api/v1/discovery/status")


@dataclass
class ThreatIntelAPI:
    _client: "PulseClient"

    def lookup(self, indicator: str):
        return self._client._post("/api/v1/threat-intel/lookup", json={"indicator": indicator})

    def list(self, page: int = 1, page_size: int = 50):
        return self._client._get("/api/v1/threat-intel/", params={"page": page, "page_size": page_size})


@dataclass
class GraphAPI:
    _client: "PulseClient"

    def overview(self):
        return self._client._get("/api/v1/graph/overview")

    def attack_paths(self, asset_id: int):
        return self._client._get(f"/api/v1/graph/attack-paths/{asset_id}")


@dataclass
class ReportsAPI:
    _client: "PulseClient"

    def executive(self):
        return self._client._get("/api/v1/reports/executive")

    def vulnerability(self):
        return self._client._get("/api/v1/reports/vulnerability")


class PulseClient:
    """BlackSentinel Pulse API Client."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip("/")
        self._token = None
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["X-API-Key"] = api_key

        self.assets = AssetsAPI(self)
        self.scans = ScansAPI(self)
        self.vulnerabilities = VulnerabilitiesAPI(self)
        self.alerts = AlertsAPI(self)
        self.dashboard = DashboardAPI(self)
        self.discovery = DiscoveryAPI(self)
        self.threat_intel = ThreatIntelAPI(self)
        self.graph = GraphAPI(self)
        self.reports = ReportsAPI(self)

    def login(self, username: str, password: str):
        resp = self._post("/api/v1/auth/login", json={"username": username, "password": password})
        self._token = resp["access_token"]
        self._headers["Authorization"] = f"Bearer {self._token}"
        return resp

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        with httpx.Client() as client:
            resp = client.request(method, url, headers=self._headers, timeout=30, **kwargs)
            if resp.status_code == 429:
                raise PulseAPIError(429, "Rate limit exceeded")
            if resp.status_code >= 400:
                try:
                    detail = resp.json().get("detail", resp.text)
                except Exception:
                    detail = resp.text
                raise PulseAPIError(resp.status_code, detail)
            return resp.json() if resp.text else {}

    def _get(self, path: str, **kwargs):
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs):
        return self._request("POST", path, **kwargs)

    def _put(self, path: str, **kwargs):
        return self._request("PUT", path, **kwargs)

    def _delete(self, path: str, **kwargs):
        return self._request("DELETE", path, **kwargs)
