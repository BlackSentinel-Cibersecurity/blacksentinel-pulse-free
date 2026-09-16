from typing import Optional

import httpx

from app.core.config import settings


class ThreatIntelLookup:
    """Look up threat intelligence indicators across multiple sources."""

    async def lookup(self, indicator: str, indicator_type: str = "auto") -> dict:
        """Look up an indicator across all configured threat intel sources."""
        if indicator_type == "auto":
            indicator_type = self._detect_type(indicator)

        results = {
            "indicator": indicator,
            "type": indicator_type,
            "sources": [],
            "is_malicious": False,
            "confidence": 0.0,
            "reports": [],
        }

        # VirusTotal
        if settings.VIRUSTOTAL_API_KEY:
            vt_result = await self._lookup_virustotal(indicator, indicator_type)
            if vt_result:
                results["sources"].append(vt_result)

        # AbuseIPDB (for IPs)
        if settings.ABUSEIPDB_API_KEY and indicator_type == "ip":
            abuse_result = await self._lookup_abuseipdb(indicator)
            if abuse_result:
                results["sources"].append(abuse_result)

        # Aggregate results
        if results["sources"]:
            malicious_votes = sum(
                1 for s in results["sources"] if s.get("is_malicious")
            )
            total_votes = len(results["sources"])
            results["is_malicious"] = malicious_votes > 0
            results["confidence"] = (
                malicious_votes / total_votes if total_votes > 0 else 0
            )

        return results

    async def _lookup_virustotal(
        self, indicator: str, indicator_type: str
    ) -> Optional[dict]:
        """Look up indicator in VirusTotal."""
        type_map = {
            "ip": "ip_addresses",
            "domain": "domains",
            "hash": "files",
            "url": "urls",
        }

        endpoint = type_map.get(indicator_type, "domains")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.virustotal.com/api/v3/{endpoint}/{indicator}",
                    headers={"x-apikey": settings.VIRUSTOTAL_API_KEY},
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    attrs = data.get("data", {}).get("attributes", {})
                    stats = attrs.get("last_analysis_stats", {})

                    malicious = stats.get("malicious", 0) + stats.get("suspicious", 0)
                    total = sum(stats.values())

                    return {
                        "source": "VirusTotal",
                        "is_malicious": malicious > 0,
                        "malicious_detections": malicious,
                        "total_engines": total,
                        "reputation": attrs.get("reputation", 0),
                        "categories": attrs.get("categories", {}),
                        "last_analysis": attrs.get("last_analysis_date"),
                    }
        except Exception:
            pass

        return None

    async def _lookup_abuseipdb(self, ip: str) -> Optional[dict]:
        """Look up IP in AbuseIPDB."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    headers={
                        "Key": settings.ABUSEIPDB_API_KEY,
                        "Accept": "application/json",
                    },
                    params={"ipAddress": ip, "maxAgeInDays": 90},
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json().get("data", {})

                    return {
                        "source": "AbuseIPDB",
                        "is_malicious": data.get("abuseConfidenceScore", 0) > 50,
                        "abuse_confidence": data.get("abuseConfidenceScore", 0),
                        "total_reports": data.get("totalReports", 0),
                        "country": data.get("countryCode"),
                        "isp": data.get("isp"),
                        "usage_type": data.get("usageType"),
                        "is_tor": data.get("isTor", False),
                        "is_whitelisted": data.get("isWhitelisted", False),
                    }
        except Exception:
            pass

        return None

    def _detect_type(self, indicator: str) -> str:
        """Auto-detect the indicator type."""
        import re

        # IP address
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", indicator):
            return "ip"

        # Hash (MD5, SHA1, SHA256)
        if re.match(r"^[a-fA-F0-9]{32}$", indicator):
            return "hash"  # MD5
        if re.match(r"^[a-fA-F0-9]{40}$", indicator):
            return "hash"  # SHA1
        if re.match(r"^[a-fA-F0-9]{64}$", indicator):
            return "hash"  # SHA256

        # URL
        if indicator.startswith(("http://", "https://")):
            return "url"

        # Domain
        if "." in indicator and " " not in indicator:
            return "domain"

        return "unknown"
