import time
from utils.loki_fetcher import fetch_logs
from utils.log_normalizer import normalize
from utils.detector import detect_anomalies
from utils.semantic_enricher import enrich_logs
from utils.utils import now_str
from utils.llm_config import USE_LLM


class AgenticMonitorAgent:
    def __init__(self, event_bus, scan_interval=30):
        self.event_bus = event_bus
        self.scan_interval = scan_interval

    def run(self):
        while True:
            self.perceive()
            time.sleep(self.scan_interval)

    def perceive(self):
        try:
            raw_logs = fetch_logs(minutes=1)
        except Exception as e:
            print("[AgenticMonitor] fetch_logs failed:", e)
            return

        try:
            logs = normalize(raw_logs)
        except Exception as e:
            print("[AgenticMonitor] normalize failed:", e)
            return

        try:
            raw_alerts, stats = detect_anomalies(logs)
        except Exception as e:
            print("[AgenticMonitor] detect_anomalies failed:", e)
            return

        if not raw_alerts:
            return

        semantic = []
        metrics = {}

        # skip LLM enrichment for pure pattern-only alerts to reduce API cost
        use_llm = USE_LLM and any(a["type"] != "RareLogPattern" for a in raw_alerts)

        try:
            semantic, metrics = enrich_logs(logs[:10], use_llm=use_llm)
        except Exception as e:
            print("[AgenticMonitor] semantic enrichment failed:", e)

        event = {
            "timestamp": time.time(),
            "alerts": raw_alerts,
            "stats": stats,
            "semantic": semantic,
            "metrics": metrics,
        }

        self.event_bus.monitor_events.put(event)
        print(f"[{now_str()}] [AgenticMonitor] Emitted {len(raw_alerts)} alerts")
