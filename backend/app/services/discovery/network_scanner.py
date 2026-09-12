import asyncio
import socket
from typing import Optional

import nmap

from app.services.discovery.base import BaseDiscoveryEngine


class NetworkDiscoveryEngine(BaseDiscoveryEngine):
    """Discover open ports, services, and network assets."""

    TOP_PORTS = {
        "top-100": "1-100",
        "top-1000": "1-1000",
        "top-10000": "1-10000",
        "full": "1-65535",
        "web": "80,443,8080,8443,8000,3000,5000,9090",
        "database": "3306,5432,1433,27017,6379,1521,9042",
        "mail": "25,110,143,465,587,993,995",
        "ssh": "22,2222",
        "common": "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1723,3389,5900,8080",
    }

    SERVICE_FINGERPRINTS = {
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        111: "RPCBind",
        135: "MSRPC",
        139: "NetBIOS",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        993: "IMAPS",
        995: "POP3S",
        1433: "MSSQL",
        1521: "Oracle",
        1723: "PPTP",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        6379: "Redis",
        8080: "HTTP-Proxy",
        8443: "HTTPS-Alt",
        27017: "MongoDB",
        9042: "Cassandra",
    }

    async def validate_target(self, target: str) -> bool:
        """Validate IP or CIDR range."""
        import ipaddress
        try:
            if "/" in target:
                ipaddress.ip_network(target, strict=False)
            else:
                ipaddress.ip_address(target)
            return True
        except ValueError:
            return False

    async def discover(self, target: str, ports: str = "top-1000", **kwargs) -> dict:
        """Scan target for open ports and services."""
        port_range = self.TOP_PORTS.get(ports, ports)

        results = {
            "target": target,
            "open_ports": [],
            "services": [],
            "hosts": [],
        }

        # Use nmap for port scanning
        nm = nmap.PortScanner()

        try:
            nm.scan(
                hosts=target,
                ports=port_range,
                arguments="-sV -sC -O --open -T4",
            )

            for host in nm.all_hosts():
                host_data = {
                    "ip": host,
                    "hostname": nm[host].hostname(),
                    "state": nm[host].state(),
                    "protocols": [],
                }

                for proto in nm[host].all_protocols():
                    ports_data = []
                    for port in nm[host][proto].keys():
                        port_info = nm[host][proto][port]
                        port_data = {
                            "port": port,
                            "state": port_info["state"],
                            "service": port_info.get("name", "unknown"),
                            "version": port_info.get("version", ""),
                            "product": port_info.get("product", ""),
                            "extra_info": port_info.get("extrainfo", ""),
                        }
                        ports_data.append(port_data)

                        # Create asset for each open port
                        self.add_asset({
                            "name": f"{host}:{port}",
                            "asset_type": "ip_address",
                            "ip_address": host,
                            "port": port,
                            "protocol": proto,
                            "service": port_info.get("name", "unknown"),
                            "version": port_info.get("version", ""),
                            "discovery_method": "port_scan",
                            "metadata": {
                                "hostname": nm[host].hostname(),
                                "os_detection": nm[host].get("osmatch", []),
                            },
                        })

                    host_data["protocols"].append({
                        "name": proto,
                        "ports": ports_data,
                    })

                results["hosts"].append(host_data)
                results["open_ports"].extend([
                    f"{p['port']}/{proto}"
                    for proto_data in host_data["protocols"]
                    for p in proto_data["ports"]
                ])

        except Exception as e:
            self.logger.error("nmap_scan_failed", target=target, error=str(e))

        return results

    async def quick_check(self, host: str, port: int) -> dict:
        """Quick single-port check."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()

            return {
                "host": host,
                "port": port,
                "open": result == 0,
                "service": self.SERVICE_FINGERPRINTS.get(port, "unknown"),
            }
        except Exception:
            return {"host": host, "port": port, "open": False, "service": "unknown"}
