import asyncio
from typing import Optional

import dns.resolver
import tldextract

from app.services.discovery.base import BaseDiscoveryEngine


class DomainDiscoveryEngine(BaseDiscoveryEngine):
    """Discover subdomains, DNS records, and related assets for a domain."""

    COMMON_SUBDOMAINS = [
        "www",
        "mail",
        "ftp",
        "smtp",
        "pop",
        "imap",
        "webmail",
        "admin",
        "portal",
        "login",
        "sso",
        "auth",
        "api",
        "dev",
        "staging",
        "test",
        "uat",
        "qa",
        "sandbox",
        "demo",
        "app",
        "apps",
        "web",
        "cdn",
        "static",
        "media",
        "blog",
        "docs",
        "wiki",
        "support",
        "help",
        "status",
        "vpn",
        "remote",
        "gateway",
        "proxy",
        "load",
        "db",
        "database",
        "mysql",
        "postgres",
        "mongo",
        "redis",
        "k8s",
        "kubernetes",
        "docker",
        "registry",
        "ci",
        "cd",
        "jenkins",
        "gitlab",
        "github",
        "monitor",
        "grafana",
        "prometheus",
        "kibana",
        "log",
        "logs",
        "elk",
        "elastic",
        "backup",
        "bak",
        "old",
        "legacy",
        "internal",
        "private",
        "corp",
        "corporate",
        "shop",
        "store",
        "pay",
        "checkout",
        "billing",
        "mx",
        "ns",
        "dns",
        "ldap",
        "kerberos",
    ]

    async def validate_target(self, target: str) -> bool:
        """Validate domain format."""
        extracted = tldextract.extract(target)
        return bool(extracted.domain and extracted.suffix)

    async def discover(self, target: str, deep: bool = False, **kwargs) -> dict:
        """Full domain discovery."""
        results = {
            "domain": target,
            "subdomains": [],
            "dns_records": {},
            "certificates": [],
            "whois": {},
            "technologies": [],
        }

        # DNS enumeration
        dns_results = await self._enumerate_dns(target)
        results["dns_records"] = dns_results

        # Subdomain brute force
        subdomains = await self._bruteforce_subdomains(target)
        results["subdomains"] = subdomains

        # Certificate Transparency
        ct_results = await self._check_certificate_transparency(target)
        results["certificates"] = ct_results

        # Combine discovered subdomains
        all_subdomains = set(subdomains)
        for cert in ct_results:
            if "subdomains" in cert:
                all_subdomains.update(cert["subdomains"])

        results["subdomains"] = list(all_subdomains)

        # Create assets for each discovered subdomain
        for subdomain in results["subdomains"]:
            self.add_asset(
                {
                    "name": subdomain,
                    "asset_type": "subdomain",
                    "parent_domain": target,
                    "discovery_method": "dns_enumeration",
                    "metadata": {
                        "dns": dns_results.get(subdomain, {}),
                    },
                }
            )

        # Add the main domain
        self.add_asset(
            {
                "name": target,
                "asset_type": "domain",
                "discovery_method": "direct",
                "metadata": {
                    "dns": dns_results.get(target, {}),
                    "subdomain_count": len(results["subdomains"]),
                },
            }
        )

        return results

    async def _enumerate_dns(self, domain: str) -> dict:
        """Enumerate DNS records for a domain."""
        records = {}
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "SRV", "CAA"]

        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type] = [
                    {
                        "value": str(rdata),
                        "ttl": answers.rrset.ttl,
                        "priority": getattr(rdata, "priority", None),
                    }
                    for rdata in answers
                ]

                # Add DNS records as assets
                for rdata in answers:
                    self.add_asset(
                        {
                            "name": f"{record_type}:{domain}",
                            "asset_type": "dns_record",
                            "record_type": record_type,
                            "value": str(rdata),
                            "domain": domain,
                            "discovery_method": "dns_enumeration",
                        }
                    )
            except (
                dns.resolver.NXDOMAIN,
                dns.resolver.NoAnswer,
                dns.resolver.NoNameservers,
            ):
                continue
            except Exception:
                continue

        return records

    async def _bruteforce_subdomains(self, domain: str) -> list[str]:
        """Bruteforce common subdomain names."""
        found = []

        async def check_subdomain(subdomain: str) -> Optional[str]:
            fqdn = f"{subdomain}.{domain}"
            try:
                dns.resolver.resolve(fqdn, "A")
                return fqdn
            except Exception:
                return None

        # Run checks concurrently with rate limiting
        semaphore = asyncio.Semaphore(20)

        async def limited_check(subdomain):
            async with semaphore:
                result = await check_subdomain(subdomain)
                if result:
                    return result
                await asyncio.sleep(0.1)
                return None

        tasks = [limited_check(sub) for sub in self.COMMON_SUBDOMAINS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if result and not isinstance(result, Exception):
                found.append(result)

        return found

    async def _check_certificate_transparency(self, domain: str) -> list[dict]:
        """Query Certificate Transparency logs for subdomains."""
        import httpx

        certificates = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"https://crt.sh/?q=%.{domain}&output=json")
                if response.status_code == 200:
                    data = response.json()
                    seen = set()
                    for entry in data:
                        name = entry.get("name_value", "")
                        subdomains = [s.strip() for s in name.split("\n") if s.strip()]
                        new_subdomains = [
                            s
                            for s in subdomains
                            if s not in seen and s.endswith(domain)
                        ]
                        seen.update(new_subdomains)

                        certificates.append(
                            {
                                "issuer": entry.get("issuer_name"),
                                "not_before": entry.get("not_before"),
                                "not_after": entry.get("not_after"),
                                "subdomains": new_subdomains,
                                "serial_number": entry.get("serial_number"),
                            }
                        )
        except Exception as e:
            self.logger.warning("ct_lookup_failed", domain=domain, error=str(e))

        return certificates
