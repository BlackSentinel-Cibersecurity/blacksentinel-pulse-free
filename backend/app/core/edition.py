"""BlackSentinel Pulse — Free / Open-Source Edition.

Real core asset discovery/inventory, capped at 25 assets. Cloud/SaaS/GitHub
discovery, threat-intel correlation, attack-graph/ML risk scoring, and
policy-driven automated remediation are paid-plan only and are not included
in this repository's source at all (endpoints/graph.py, threat_intel.py,
policies.py) — see blacksentinel.io for the full platform.
"""

from __future__ import annotations

from dataclasses import dataclass

# Discovery types available on the free plan — basic, no third-party API
# cost. 'cloud' (AWS/Azure/GCP), 'saas', and GitHub secret scanning are
# paid-tier only and aren't wired up in this repo at all.
FREE_DISCOVERY_TYPES = {"passive", "dns", "active"}


@dataclass(frozen=True)
class EditionLimits:
    max_assets: int


LIMITS = EditionLimits(max_assets=25)
EDITION = "free"
