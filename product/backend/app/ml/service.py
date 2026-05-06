import numpy as np
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

EVENT_TYPES = [
    "network_scan", "brute_force", "malware_detected", "privilege_escalation",
    "data_exfiltration", "traffic_burst", "c2_communication", "lateral_movement",
    "ddos", "port_scan", "suspicious_login", "file_access", "config_change",
    "unknown",
]

SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4, "warning": 1}


class AnomalyDetector:
    def __init__(self, contamination=0.1, n_estimators=100):
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=42,
        )
        self.event_type_encoder = LabelEncoder()
        self.is_fitted = False
        self.event_type_encoder.fit(EVENT_TYPES)

    def _encode_event(self, event: dict) -> list:
        severity = SEVERITY_ORDER.get(event.get("severity", "info").lower(), 1)

        event_type = event.get("event_type", "unknown")
        try:
            event_type_idx = self.event_type_encoder.transform([event_type])[0]
        except ValueError:
            event_type_idx = len(EVENT_TYPES)

        observed_at = event.get("observed_at", "")
        hour = 12
        minute = 0
        if observed_at:
            try:
                dt = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
                hour = dt.hour
                minute = dt.minute
            except (ValueError, AttributeError):
                pass

        source_ip_hash = hash(event.get("source_ip", "")) % 100
        target_ip_hash = hash(event.get("target_ip", "")) % 100

        return [severity, event_type_idx, hour, minute, source_ip_hash, target_ip_hash]

    def fit(self, events: list[dict]) -> None:
        if len(events) < 10:
            return

        X = np.array([self._encode_event(e) for e in events])
        self.model.fit(X)
        self.is_fitted = True

    def predict(self, events: list[dict]) -> list[dict]:
        if not self.is_fitted or len(events) < 1:
            return [{"event": e, "anomaly_score": 0.0, "is_anomaly": False} for e in events]

        X = np.array([self._encode_event(e) for e in events])
        predictions = self.model.predict(X)
        scores = self.model.decision_function(X)

        results = []
        for event, pred, score in zip(events, predictions, scores):
            normalized_score = float((score + 1) / 2)
            normalized_score = max(0.0, min(1.0, normalized_score))
            anomaly_score = round(1.0 - normalized_score, 3)
            is_anomaly = int(pred) == -1

            results.append({
                "event": event,
                "anomaly_score": anomaly_score,
                "is_anomaly": is_anomaly,
            })

        return results

    def get_anomaly_summary(self, events: list[dict]) -> dict:
        if not events:
            return {"total": 0, "anomalies": 0, "anomaly_rate": 0.0, "avg_score": 0.0}

        results = self.predict(events)
        anomalies = [r for r in results if r["is_anomaly"]]
        scores = [r["anomaly_score"] for r in results]

        return {
            "total": len(results),
            "anomalies": len(anomalies),
            "anomaly_rate": round(len(anomalies) / len(results), 3),
            "avg_score": round(sum(scores) / len(scores), 3),
        }


anomaly_detector = AnomalyDetector()
