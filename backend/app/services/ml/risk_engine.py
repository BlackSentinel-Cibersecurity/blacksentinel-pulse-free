import numpy as np
from datetime import datetime


class RiskScoringEngine:
    """
    AI-powered risk scoring engine for BlackSentinel Pulse.

    Calculates composite risk scores based on multiple factors:
    - Vulnerability severity and exploitability
    - Asset exposure and accessibility
    - Business criticality
    - Threat intelligence correlation
    - Asset age and patch currency
    - Configuration weaknesses
    """

    DEFAULT_WEIGHTS = {
        "vulnerability": 0.25,
        "exposure": 0.20,
        "criticality": 0.20,
        "threat_intel": 0.15,
        "configuration": 0.10,
        "age": 0.05,
        "network_position": 0.05,
    }

    ASSET_TYPE_CRITICALITY = {
        "domain": 70,
        "subdomain": 60,
        "ip_address": 65,
        "web_application": 80,
        "api_endpoint": 85,
        "cloud_resource": 75,
        "database": 95,
        "kubernetes": 90,
        "container": 70,
        "serverless": 70,
        "dns_record": 40,
        "ssl_certificate": 60,
        "email_server": 80,
        "vpn": 90,
        "firewall": 85,
        "repository": 75,
        "ci_cd_pipeline": 80,
        "identity_provider": 95,
        "saas_application": 70,
    }

    def __init__(self, weights: dict = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def calculate_risk_score(self, asset_data: dict) -> dict:
        """Calculate comprehensive risk score for an asset."""
        scores = {
            "vulnerability": self._score_vulnerabilities(asset_data),
            "exposure": self._score_exposure(asset_data),
            "criticality": self._score_criticality(asset_data),
            "threat_intel": self._score_threat_intel(asset_data),
            "configuration": self._score_configuration(asset_data),
            "age": self._score_age(asset_data),
            "network_position": self._score_network_position(asset_data),
        }

        # Calculate weighted composite score
        composite = sum(scores[factor] * self.weights[factor] for factor in scores)

        # Apply multipliers for critical conditions
        composite = self._apply_critical_multipliers(composite, asset_data)

        # Clamp to 0-100
        composite = max(0, min(100, composite))

        return {
            "risk_score": round(composite, 2),
            "risk_level": self._get_risk_level(composite),
            "factors": scores,
            "weights": self.weights,
            "recommendations": self._generate_recommendations(scores, asset_data),
            "calculated_at": datetime.utcnow().isoformat(),
        }

    def _score_vulnerabilities(self, asset: dict) -> float:
        """Score based on associated vulnerabilities."""
        vulns = asset.get("vulnerabilities", [])
        if not vulns:
            return 10  # No vulnerabilities = low risk from this factor

        critical = sum(1 for v in vulns if v.get("severity") == "critical")
        high = sum(1 for v in vulns if v.get("severity") == "high")
        medium = sum(1 for v in vulns if v.get("severity") == "medium")
        exploitable = sum(1 for v in vulns if v.get("exploit_available"))

        score = (
            critical * 25
            + high * 15
            + medium * 8
            + exploitable * 20
            + min(len(vulns) * 2, 20)  # Volume factor
        )

        return min(100, score)

    def _score_exposure(self, asset: dict) -> float:
        """Score based on external exposure."""
        score = 0

        # Internet-facing assets score higher
        if asset.get("is_internet_facing", False):
            score += 40
        elif asset.get("is_public", False):
            score += 30

        # Open ports
        open_ports = asset.get("open_ports", [])
        score += min(len(open_ports) * 5, 30)

        # Exposed services
        high_risk_services = [
            "ssh",
            "rdp",
            "ftp",
            "telnet",
            "mysql",
            "redis",
            "mongodb",
        ]
        for port_info in open_ports:
            if port_info.get("service", "").lower() in high_risk_services:
                score += 10

        # No authentication
        if asset.get("requires_auth") is False:
            score += 15

        return min(100, score)

    def _score_criticality(self, asset: dict) -> float:
        """Score based on business criticality."""
        asset_type = asset.get("asset_type", "unknown")
        base_criticality = self.ASSET_TYPE_CRITICALITY.get(asset_type, 50)

        # Adjust based on tags
        tags = [t.lower() for t in asset.get("tags", [])]
        if "production" in tags or "prod" in tags:
            base_criticality = min(100, base_criticality + 20)
        if "critical" in tags:
            base_criticality = min(100, base_criticality + 15)
        if "internal" in tags:
            base_criticality = max(0, base_criticality - 10)
        if "development" in tags or "dev" in tags:
            base_criticality = max(0, base_criticality - 20)

        # Customer-facing assets are more critical
        if asset.get("customer_facing"):
            base_criticality = min(100, base_criticality + 15)

        return base_criticality

    def _score_threat_intel(self, asset: dict) -> float:
        """Score based on threat intelligence matches."""
        threats = asset.get("threat_intel", [])
        if not threats:
            return 5  # No threat intel = low score

        score = 0
        for threat in threats:
            confidence = threat.get("confidence", 0)
            threat_type = threat.get("threat_type", "")

            if threat_type in ("malware", "ransomware", "apt"):
                score += confidence * 40
            elif threat_type in ("c2", "botnet"):
                score += confidence * 30
            elif threat_type in ("phishing", "credential_stuffing"):
                score += confidence * 25
            else:
                score += confidence * 15

        return min(100, score)

    def _score_configuration(self, asset: dict) -> float:
        """Score based on security configuration issues."""
        score = 0

        # SSL/TLS issues
        ssl_info = asset.get("ssl_info", {})
        if ssl_info.get("is_expired"):
            score += 25
        if ssl_info.get("weak_cipher"):
            score += 15
        if not ssl_info.get("hsts_enabled"):
            score += 10

        # DNS issues
        dns = asset.get("dns_records", {})
        if not dns.get("has_spf"):
            score += 10
        if not dns.get("has_dmarc"):
            score += 10

        # Cloud misconfigurations
        misconfigs = asset.get("misconfigurations", [])
        score += min(len(misconfigs) * 10, 30)

        # Missing security headers
        headers = asset.get("security_headers", {})
        if not headers.get("x_content_type_options"):
            score += 5
        if not headers.get("x_frame_options"):
            score += 5
        if not headers.get("content_security_policy"):
            score += 5

        return min(100, score)

    def _score_age(self, asset: dict) -> float:
        """Score based on asset age and patch currency."""
        score = 0

        # Old assets without updates
        last_updated = asset.get("last_updated")
        if last_updated:
            try:
                updated = datetime.fromisoformat(last_updated)
                days_since = (datetime.utcnow() - updated).days
                if days_since > 365:
                    score += 30
                elif days_since > 180:
                    score += 20
                elif days_since > 90:
                    score += 10
            except (ValueError, TypeError):
                pass

        # Unpatched software
        software_age = asset.get("software_age_days", 0)
        if software_age > 365:
            score += 25
        elif software_age > 180:
            score += 15

        return min(100, score)

    def _score_network_position(self, asset: dict) -> float:
        """Score based on network position and connectivity."""
        score = 0

        # DMZ assets
        if asset.get("network_zone") == "dmz":
            score += 30

        # Direct internet exposure
        if asset.get("behind_waf") is False:
            score += 15

        # High number of connections
        connection_count = asset.get("connection_count", 0)
        if connection_count > 100:
            score += 20
        elif connection_count > 50:
            score += 10

        return min(100, score)

    def _apply_critical_multipliers(self, score: float, asset: dict) -> float:
        """Apply multipliers for critical conditions."""
        multiplier = 1.0

        # Active exploitation in the wild
        if asset.get("exploit_in_wild"):
            multiplier *= 1.3

        # Critical data store
        if asset.get("contains_pii") or asset.get("contains_phi"):
            multiplier *= 1.2

        # Compliance violation
        if asset.get("compliance_violations"):
            multiplier *= 1.15

        return score * multiplier

    def _get_risk_level(self, score: float) -> str:
        """Get risk level from score."""
        if score >= 90:
            return "critical"
        elif score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        return "info"

    def _generate_recommendations(self, scores: dict, asset: dict) -> list[str]:
        """Generate actionable recommendations based on scores."""
        recommendations = []

        if scores["vulnerability"] > 60:
            recommendations.append(
                "RemEDIATE critical and high-severity vulnerabilities immediately"
            )
        if scores["exposure"] > 60:
            recommendations.append(
                "Reduce attack surface by removing unnecessary public exposure"
            )
        if scores["threat_intel"] > 40:
            recommendations.append(
                "Investigate threat intelligence matches and isolate if necessary"
            )
        if scores["configuration"] > 40:
            recommendations.append(
                "Fix security configuration issues (SSL, headers, DNS)"
            )
        if scores["age"] > 40:
            recommendations.append("Update software and apply latest patches")
        if scores["network_position"] > 40:
            recommendations.append("Review network segmentation and access controls")

        return recommendations

    def predict_risk_trend(self, historical_scores: list[dict]) -> dict:
        """Predict risk score trend using simple ML."""
        if len(historical_scores) < 3:
            return {"trend": "insufficient_data", "prediction": None}

        scores = [s["risk_score"] for s in historical_scores]
        x = np.arange(len(scores))

        # Simple linear regression
        coeffs = np.polyfit(x, scores, 1)
        slope = coeffs[0]

        # Predict next 7 days
        future_x = np.arange(len(scores), len(scores) + 7)
        predictions = np.polyval(coeffs, future_x)

        trend = (
            "increasing" if slope > 0.5 else "decreasing" if slope < -0.5 else "stable"
        )

        return {
            "trend": trend,
            "slope": round(float(slope), 4),
            "current_score": scores[-1],
            "predicted_scores": [round(float(p), 2) for p in predictions],
            "confidence": max(0, min(1, 1 - abs(slope) / 10)),
        }
