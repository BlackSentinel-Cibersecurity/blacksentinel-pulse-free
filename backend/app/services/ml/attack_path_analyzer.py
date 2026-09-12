from typing import Any
from app.core.database import Neo4jDriver


class AttackPathAnalyzer:
    """
    Analyzes and predicts attack paths through the infrastructure.

    Uses graph theory and ML to:
    - Find shortest paths between entry points and critical assets
    - Calculate attack complexity scores
    - Identify chokepoints and critical nodes
    - Predict likely attack scenarios
    """

    async def find_all_paths(
        self,
        org_id: int,
        max_depth: int = 6,
        min_risk: float = 20.0,
    ) -> list[dict]:
        """Find all significant attack paths in the infrastructure."""
        driver = await Neo4jDriver.get_driver()

        async with driver.session() as session:
            query = """
            MATCH path = (entry:Asset)-[*1..$depth]->(target:Asset)
            WHERE entry.organization_id = $org_id
            AND target.organization_id = $org_id
            AND entry.is_entry_point = true
            AND target.criticality IN ['critical', 'high']
            AND ALL(n IN nodes(path) WHERE n.risk_score >= $min_risk)
            WITH path,
                 [n IN nodes(path) | n] as path_nodes,
                 [r IN relationships(path) | r] as path_rels,
                 reduce(score = 0.0, r IN relationships(path) |
                    score + coalesce(r.risk_score, 10)) as path_risk,
                 length(path) as path_length
            RETURN path_nodes, path_rels, path_risk, path_length
            ORDER BY path_risk DESC
            LIMIT 100
            """

            result = await session.run(
                query,
                org_id=org_id,
                depth=max_depth,
                min_risk=min_risk,
            )

            paths = []
            async for record in result:
                path_nodes = record["path_nodes"]
                path_rels = record["path_rels"]

                steps = []
                for i, node in enumerate(path_nodes):
                    step = {
                        "asset_id": node.get("pulse_id"),
                        "name": node.get("name"),
                        "type": node.get("asset_type"),
                        "risk_score": node.get("risk_score", 0),
                    }
                    if i < len(path_rels):
                        rel = path_rels[i]
                        step["relationship"] = {
                            "type": rel.get("type"),
                            "risk_score": rel.get("risk_score", 0),
                        }
                    steps.append(step)

                paths.append({
                    "path_id": f"path_{len(paths)}",
                    "steps": steps,
                    "total_risk": record["path_risk"],
                    "length": record["path_length"],
                    "complexity": self._calculate_complexity(record["path_risk"], record["path_length"]),
                    "entry_point": path_nodes[0].get("name"),
                    "target": path_nodes[-1].get("name"),
                })

        return paths

    async def find_criticalchokepoints(self, org_id: int) -> list[dict]:
        """Find critical chokepoints - assets that appear in many attack paths."""
        driver = await Neo4jDriver.get_driver()

        async with driver.session() as session:
            query = """
            MATCH (entry:Asset {is_entry_point: true})-[*1..6]->(target:Asset)
            WHERE entry.organization_id = $org_id
            UNWIND nodes(path) as node
            RETURN node.pulse_id as id, node.name as name,
                   node.asset_type as type, node.risk_score as risk_score,
                   count(*) as path_count
            ORDER BY path_count DESC
            LIMIT 20
            """

            result = await session.run(query, org_id=org_id)
            chokepoints = []
            async for record in result:
                chokepoints.append({
                    "asset_id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "risk_score": record["risk_score"],
                    "paths_through": record["path_count"],
                    "importance_score": record["path_count"] * (record["risk_score"] or 0),
                })

        return chokepoints

    async def calculate_blast_radius(
        self,
        asset_id: str,
        max_depth: int = 3,
    ) -> dict:
        """Calculate the blast radius if an asset is compromised."""
        driver = await Neo4jDriver.get_driver()

        async with driver.session() as session:
            query = """
            MATCH (start:Asset {pulse_id: $asset_id})-[*1..$depth]->(affected:Asset)
            RETURN DISTINCT
                affected.pulse_id as id,
                affected.name as name,
                affected.asset_type as type,
                affected.risk_score as risk_score,
                affected.criticality as criticality
            ORDER BY affected.risk_score DESC
            """

            result = await session.run(
                query,
                asset_id=asset_id,
                depth=max_depth,
            )

            affected = []
            async for record in result:
                affected.append({
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "risk_score": record["risk_score"],
                    "criticality": record["criticality"],
                })

        # Calculate blast radius score
        total_risk = sum(a.get("risk_score", 0) for a in affected)
        critical_count = sum(1 for a in affected if a.get("criticality") == "critical")
        blast_score = min(100, len(affected) * 5 + critical_count * 20 + total_risk / 10)

        return {
            "source_asset": asset_id,
            "blast_radius": blast_score,
            "affected_count": len(affected),
            "critical_affected": critical_count,
            "affected_assets": affected,
            "severity": "critical" if blast_score > 80 else "high" if blast_score > 60 else "medium" if blast_score > 40 else "low",
        }

    async def suggest_mitigations(self, attack_path: dict) -> list[dict]:
        """Suggest mitigations for a specific attack path."""
        mitigations = []
        steps = attack_path.get("steps", [])

        for i, step in enumerate(steps):
            asset_type = step.get("type")
            risk_score = step.get("risk_score", 0)
            relationship = step.get("relationship", {}).get("type", "")

            if asset_type == "web_application" and risk_score > 60:
                mitigations.append({
                    "step": i,
                    "asset": step.get("name"),
                    "mitigation": "Implement WAF and review application security",
                    "priority": "high",
                    "effort": "medium",
                })

            if relationship == "POINTS_TO" and risk_score > 50:
                mitigations.append({
                    "step": i,
                    "asset": step.get("name"),
                    "mitigation": "Review and restrict network connectivity",
                    "priority": "medium",
                    "effort": "low",
                })

            if asset_type == "cloud_resource" and step.get("metadata", {}).get("public_ip"):
                mitigations.append({
                    "step": i,
                    "asset": step.get("name"),
                    "mitigation": "Remove public IP or restrict access via security groups",
                    "priority": "high",
                    "effort": "low",
                })

        return sorted(mitigations, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])

    def _calculate_complexity(self, total_risk: float, path_length: int) -> str:
        """Calculate attack complexity from path metrics."""
        complexity_score = total_risk / max(path_length, 1)

        if complexity_score > 40:
            return "low"  # Easy to exploit
        elif complexity_score > 20:
            return "medium"
        else:
            return "high"  # Hard to exploit
