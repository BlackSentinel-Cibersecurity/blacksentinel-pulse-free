import numpy as np
from datetime import datetime


class AnomalyDetector:
    """
    ML-based anomaly detection for the attack surface.

    Detects unusual patterns in:
    - New asset discoveries
    - Configuration changes
    - Traffic patterns
    - Vulnerability trends
    - User behavior
    """

    def __init__(self):
        self.baseline = {}
        self.thresholds = {
            "asset_discovery_rate": {"mean": 10, "std": 5, "sensitivity": 2.0},
            "vulnerability_rate": {"mean": 5, "std": 3, "sensitivity": 2.5},
            "risk_score_change": {"mean": 0, "std": 10, "sensitivity": 3.0},
            "port_scan_frequency": {"mean": 2, "std": 1, "sensitivity": 2.0},
            "dns_change_frequency": {"mean": 1, "std": 0.5, "sensitivity": 2.0},
        }

    def update_baseline(self, metric: str, values: list[float]):
        """Update baseline statistics for a metric."""
        if len(values) < 10:
            return

        self.baseline[metric] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "median": float(np.median(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75)),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def detect_anomaly(self, metric: str, value: float) -> dict:
        """Detect if a value is anomalous for the given metric."""
        baseline = self.baseline.get(metric)
        threshold = self.thresholds.get(metric, {"sensitivity": 2.0})

        if not baseline:
            return {
                "is_anomaly": False,
                "confidence": 0,
                "message": "No baseline data available",
            }

        mean = baseline["mean"]
        std = baseline["std"]
        sensitivity = threshold["sensitivity"]

        if std == 0:
            z_score = 0 if value == mean else float("inf")
        else:
            z_score = (value - mean) / std

        is_anomaly = abs(z_score) > sensitivity
        confidence = min(1.0, abs(z_score) / (sensitivity * 2))

        return {
            "is_anomaly": is_anomaly,
            "z_score": round(float(z_score), 4),
            "confidence": round(confidence, 4),
            "value": value,
            "baseline_mean": round(mean, 4),
            "baseline_std": round(std, 4),
            "deviation": "above" if z_score > 0 else "below",
            "message": f"Value is {'anomalously high' if z_score > sensitivity else 'anomalously low' if z_score < -sensitivity else 'within normal range'}",
        }

    def detect_asset_anomalies(self, asset_history: list[dict]) -> list[dict]:
        """Detect anomalies in asset behavior over time."""
        anomalies = []

        if len(asset_history) < 5:
            return anomalies

        # Check for sudden risk score changes
        risk_scores = [h.get("risk_score", 0) for h in asset_history]
        for i in range(1, len(risk_scores)):
            change = risk_scores[i] - risk_scores[i - 1]
            if abs(change) > 20:
                anomalies.append(
                    {
                        "type": "risk_score_spike",
                        "severity": "high" if change > 30 else "medium",
                        "description": f"Risk score changed by {change:+.1f} points",
                        "timestamp": asset_history[i].get("timestamp"),
                        "details": {
                            "previous": risk_scores[i - 1],
                            "current": risk_scores[i],
                            "change": change,
                        },
                    }
                )

        # Check for new open ports
        for i in range(1, len(asset_history)):
            prev_ports = set(asset_history[i - 1].get("open_ports", []))
            curr_ports = set(asset_history[i].get("open_ports", []))
            new_ports = curr_ports - prev_ports
            if new_ports:
                anomalies.append(
                    {
                        "type": "new_exposure",
                        "severity": "high",
                        "description": f"New open ports detected: {', '.join(map(str, new_ports))}",
                        "timestamp": asset_history[i].get("timestamp"),
                        "details": {"new_ports": list(new_ports)},
                    }
                )

        # Check for technology changes
        for i in range(1, len(asset_history)):
            prev_tech = set(asset_history[i - 1].get("technologies", []))
            curr_tech = set(asset_history[i].get("technologies", []))
            new_tech = curr_tech - prev_tech
            removed_tech = prev_tech - curr_tech
            if new_tech or removed_tech:
                anomalies.append(
                    {
                        "type": "technology_change",
                        "severity": "low",
                        "description": f"Technology stack changed: +{list(new_tech)} -{list(removed_tech)}",
                        "timestamp": asset_history[i].get("timestamp"),
                        "details": {
                            "added": list(new_tech),
                            "removed": list(removed_tech),
                        },
                    }
                )

        return anomalies

    def detect_network_anomalies(self, traffic_data: list[dict]) -> list[dict]:
        """Detect anomalies in network traffic patterns."""
        anomalies = []

        if len(traffic_data) < 10:
            return anomalies

        # Analyze connection patterns
        connections_per_hour = [d.get("connections", 0) for d in traffic_data]
        self.update_baseline("connections_per_hour", connections_per_hour)

        latest = connections_per_hour[-1]
        result = self.detect_anomaly("connections_per_hour", latest)
        if result["is_anomaly"]:
            anomalies.append(
                {
                    "type": "traffic_anomaly",
                    "severity": "high" if result["deviation"] == "above" else "medium",
                    "description": f"Unusual traffic volume detected: {latest} connections (baseline: {result['baseline_mean']:.0f})",
                    "confidence": result["confidence"],
                }
            )

        # Analyze geographic distribution
        geo_data = {}
        for d in traffic_data:
            for country in d.get("countries", []):
                geo_data[country] = geo_data.get(country, 0) + 1

        # Check for new countries
        if traffic_data:
            latest_countries = set(traffic_data[-1].get("countries", []))
            all_countries = set()
            for d in traffic_data[:-1]:
                all_countries.update(d.get("countries", []))

            new_countries = latest_countries - all_countries
            if new_countries:
                anomalies.append(
                    {
                        "type": "geo_anomaly",
                        "severity": "medium",
                        "description": f"New geographic sources: {', '.join(new_countries)}",
                    }
                )

        return anomalies

    def predict_failure(self, system_metrics: list[dict]) -> dict:
        """Predict potential system failures based on metrics."""
        if len(system_metrics) < 20:
            return {"prediction": "insufficient_data"}

        # Analyze trends
        cpu_usage = [m.get("cpu", 0) for m in system_metrics]
        memory_usage = [m.get("memory", 0) for m in system_metrics]
        disk_usage = [m.get("disk", 0) for m in system_metrics]

        # Calculate trends
        x = np.arange(len(cpu_usage))
        cpu_trend = np.polyfit(x, cpu_usage, 1)[0]
        mem_trend = np.polyfit(x, memory_usage, 1)[0]
        disk_trend = np.polyfit(x, disk_usage, 1)[0]

        # Predict time to threshold
        predictions = {}
        for name, values, trend in [
            ("cpu", cpu_usage, cpu_trend),
            ("memory", memory_usage, mem_trend),
            ("disk", disk_usage, disk_trend),
        ]:
            if trend > 0:
                current = values[-1]
                remaining = 100 - current
                hours_to_threshold = (
                    remaining / (trend * 60) if trend > 0 else float("inf")
                )
                predictions[name] = {
                    "current": round(current, 1),
                    "trend": "increasing",
                    "hours_to_100": round(hours_to_threshold, 1)
                    if hours_to_threshold < 168
                    else None,
                    "risk": "high"
                    if current > 80 or hours_to_threshold < 24
                    else "medium"
                    if current > 60
                    else "low",
                }
            else:
                predictions[name] = {
                    "current": round(values[-1], 1),
                    "trend": "stable_or_decreasing",
                    "risk": "low",
                }

        return {
            "predictions": predictions,
            "overall_risk": max(p["risk"] for p in predictions.values()),
            "recommendations": self._generate_system_recommendations(predictions),
        }

    def _generate_system_recommendations(self, predictions: dict) -> list[str]:
        """Generate system-level recommendations."""
        recs = []
        for name, pred in predictions.items():
            if pred.get("risk") == "high":
                if name == "cpu":
                    recs.append(
                        "CPU usage trending high - consider scaling up or optimizing workloads"
                    )
                elif name == "memory":
                    recs.append(
                        "Memory usage trending high - check for memory leaks or increase allocation"
                    )
                elif name == "disk":
                    recs.append(
                        "Disk usage trending high - clean up logs and old data or expand storage"
                    )
        return recs
