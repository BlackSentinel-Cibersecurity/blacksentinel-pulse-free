# BlackSentinel Pulse Python SDK

## Installation

```bash
pip install httpx
```

## Quick Start

```python
from blacksentinel import PulseClient

# Connect and authenticate
client = PulseClient(base_url="http://localhost:8000")
client.login("admin", "admin123")

# Or use API key
client = PulseClient(base_url="http://localhost:8000", api_key="ps_your_api_key")
```

## Assets

```python
# List all assets
assets = client.assets.list(page=1, page_size=10)
print(f"Total assets: {assets['total']}")

# Get specific asset
asset = client.assets.get(asset_id=1)

# Create asset
new_asset = client.assets.create(
    name="example.com",
    asset_type="domain",
    tags=["production"]
)

# Delete asset
client.assets.delete(asset_id=1)
```

## Scans

```python
# List scans
scans = client.scans.list(page=1)

# Start a scan
scan = client.scans.create(
    name="Quick scan",
    scan_type="full_discovery",
    targets=["example.com", "10.0.0.1"]
)

# Get scan details
details = client.scans.get(scan_id=scan["id"])

# Cancel scan
client.scans.cancel(scan_id=scan["id"])
```

## Vulnerabilities

```python
# List vulnerabilities
vulns = client.vulnerabilities.list(page=1, page_size=20)

# Get specific vulnerability
vuln = client.vulnerabilities.get(vuln_id=1)
```

## Alerts

```python
# List alerts
alerts = client.alerts.list(page=1)

# Acknowledge alert
client.alerts.acknowledge(alert_id=1)

# Resolve alert
client.alerts.resolve(alert_id=1, notes="Fixed by updating config")
```

## Dashboard

```python
# Get summary stats
summary = client.dashboard.summary()
print(f"Total assets: {summary['total_assets']}")
print(f"Critical vulns: {summary['critical_vulnerabilities']}")

# Risk overview
risk = client.dashboard.risk_overview()
```

## Discovery

```python
# Start discovery
result = client.discovery.start(
    discovery_type="domain",
    targets=["example.com"]
)

# Check status
status = client.discovery.status()
```

## Threat Intelligence

```python
# Lookup indicator
ti = client.threat_intel.lookup(indicator="1.2.3.4")

# List threat intel entries
entries = client.threat_intel.list(page=1)
```

## Attack Paths

```python
# Get attack surface graph
graph = client.graph.overview()

# Get attack paths for asset
paths = client.graph.attack_paths(asset_id=1)
```

## Reports

```python
# Generate executive report
exec_report = client.reports.executive()

# Generate vulnerability report
vuln_report = client.reports.vulnerability()
```

## Error Handling

```python
from blacksentinel import PulseClient, PulseAPIError

client = PulseClient(base_url="http://localhost:8000")

try:
    client.login("admin", "wrong_password")
except PulseAPIError as e:
    print(f"Error {e.status_code}: {e.detail}")
```
