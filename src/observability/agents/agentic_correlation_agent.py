import time
from utils.utils import now_str

ALERT_CATEGORY_MAP = {
    "ErrorSpike": "application",
    "TimeoutSpike": "dependency",
    "RareLogPattern": "anomaly",
    "DependencyDegradation": "dependency",
}


class AgenticCorrelationAgent:
    def __init__(self, event_bus, suppression_window=120):
        self.event_bus = event_bus
        self.suppression_window = suppression_window
        self.last_incident_signature_time = {}

    def run(self):
        while True:
            event = self.event_bus.monitor_events.get()
            self.correlate(event)

    def correlate(self, event):
        categories = set()
        for alert in event.get("alerts", []):
            category = ALERT_CATEGORY_MAP.get(alert.get("type"), "unknown")
            categories.add(category)

        signature = frozenset(categories)
        now = time.time()

        # suppress duplicate incidents within the suppression window
        if now - self.last_incident_signature_time.get(signature, 0) < self.suppression_window:
            return

        incident = {
            "incident_id": f"INC-{int(now)}",
            "categories": list(categories),
            "event_count": len(event.get("alerts", [])),
            "created_at": now,
            "metrics": event.get("metrics", {}),
            "semantic": event.get("semantic", []),
            "stats": event.get("stats", {}),
        }

        self.event_bus.incidents.put(incident)
        self.last_incident_signature_time[signature] = now
        print(f"[{now_str()}] [AgenticCorrelation] Incident created")
