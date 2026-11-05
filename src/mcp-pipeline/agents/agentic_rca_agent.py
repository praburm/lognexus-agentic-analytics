import time
import json
import os
from utils.utils import now_str
from utils.llm_config import USE_LLM
from utils.notifier_pushover import send_push


def load_llm_rca():
    if not USE_LLM:
        return None
    try:
        from utils.llm_rca import llm_rca as _llm_rca
        return _llm_rca
    except Exception as e:
        print("[AgenticRCA] LLM import failed:", e)
        return None


LLM_RCA = load_llm_rca()


class AgenticRCAAgent:
    def __init__(self, event_bus, output_dir="data/incidents"):
        self.event_bus = event_bus
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        while True:
            incident = self.event_bus.incidents.get()
            self.analyze(incident)

    def analyze(self, incident):
        categories = list(incident.get("categories", []))
        causes = []

        if "application" in categories:
            causes.append({
                "cause": "Application error spike",
                "confidence": 0.7,
                "action": "Inspect recent deployments and logs",
            })

        if "dependency" in categories:
            causes.append({
                "cause": "Downstream dependency timeout",
                "confidence": 0.8,
                "action": "Check dependency health and latency",
            })

        if "anomaly" in categories:
            causes.append({
                "cause": "Rare or unexpected behavior",
                "confidence": 0.6,
                "action": "Inspect anomalous logs",
            })

        if not causes:
            causes.append({
                "cause": "Unclassified anomaly",
                "confidence": 0.4,
                "action": "Review raw logs",
            })

        rca_result = {
            "incident_id": incident.get("incident_id"),
            "categories": categories,
            "rule_based_rca": causes,
            "analyzed_at": time.time(),
        }

        if "metrics" in incident:
            rca_result["metrics"] = incident["metrics"]

        if LLM_RCA:
            try:
                # trim payload to avoid token limits
                lightweight_incident = {
                    "incident_id": incident.get("incident_id"),
                    "categories": incident.get("categories"),
                    "metrics": incident.get("metrics"),
                    "alerts": incident.get("alerts", [])[:3],
                }
                rca_result["llm_rca"] = LLM_RCA(lightweight_incident)
            except Exception:
                rca_result["llm_skipped"] = "LLM RCA skipped due to payload size or rate limits"

        self._persist_rca(rca_result)

        print(f"\n[{now_str()}] RCA RESULT")
        print(json.dumps(rca_result, indent=2))
        print_rca_table(rca_result)

        send_push(rca_result)

    def _persist_rca(self, rca_result):
        incident_id = rca_result.get("incident_id", "unknown")
        path = os.path.join(self.output_dir, f"{incident_id}.json")
        try:
            with open(path, "w") as f:
                json.dump(rca_result, f, indent=2)
        except Exception as e:
            print("[AgenticRCA] Failed to persist RCA:", e)


def print_rca_table(rca):
    print("\nRCA SUMMARY")
    print("+----------------------+------------------------------------------+")
    print("| Field                | Value                                    |")
    print("+----------------------+------------------------------------------+")
    print(f"| Incident ID          | {rca.get('incident_id', ''):<40} |")
    print(f"| Categories           | {', '.join(rca.get('categories', [])):<40} |")

    for i, r in enumerate(rca.get("rule_based_rca", []), 1):
        print("+----------------------+------------------------------------------+")
        print(f"| Rule Cause {i}         | {r.get('cause', ''):<40} |")
        print(f"| Confidence           | {r.get('confidence', ''):<40} |")
        print(f"| Action               | {r.get('action', ''):<40} |")

    llm = rca.get("llm_rca", {}).get("analysis")
    if llm:
        print("+----------------------+------------------------------------------+")
        print(f"| LLM Root Cause       | {llm.get('root_cause', '')[:40]:<40} |")
        print(f"| LLM Confidence       | {llm.get('confidence', ''):<40} |")
        for i, act in enumerate(llm.get("recommended_actions", []), 1):
            print(f"| LLM Action {i:<10} | {act[:40]:<40} |")

    if rca.get("llm_skipped"):
        print("+----------------------+------------------------------------------+")
        print(f"| LLM Status           | {rca['llm_skipped']:<40} |")

    print("+----------------------+------------------------------------------+\n")
