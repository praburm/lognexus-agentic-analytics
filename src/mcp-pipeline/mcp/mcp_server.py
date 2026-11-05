import sys
import os
import json
import time
import hashlib
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from mcp.server.fastmcp import FastMCP
    _HAS_MCP = True
except ImportError:
    _HAS_MCP = False
    class _FakeMCP:
        def __init__(self, *a, **kw): pass
        def tool(self):
            def dec(fn): return fn
            return dec
        def run(self): pass
    FastMCP = _FakeMCP

mcp = FastMCP("LogAnalytics")

_SERVICES = ["payment-svc", "api-gateway", "auth-service", "order-processor", "inventory-svc"]
_PODS = {
    "payment-svc":     "payment-svc-7d9f8b-xkp9n",
    "api-gateway":     "api-gateway-4c2a1b-m2nf4",
    "auth-service":    "auth-service-9e3f5c-q9r3t",
    "order-processor": "order-processor-2b8d6a-v5l8k",
    "inventory-svc":   "inventory-svc-1a7e4f-w1j7p",
}


def _ts(offset_sec: int = 0) -> str:
    return datetime.utcfromtimestamp(time.time() - offset_sec).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_samples() -> dict:
    error_spike = "\n".join([
        *[json.dumps({"timestamp": _ts(300 - i * 5), "level": "error",
                      "service": "payment-svc", "pod": _PODS["payment-svc"],
                      "message": f"Database connection timeout: failed to acquire from pool after 5000ms (attempt {i+1})"})
          for i in range(12)],
        *[json.dumps({"timestamp": _ts(200 - i * 3), "level": "error",
                      "service": "payment-svc", "pod": _PODS["payment-svc"],
                      "message": "NullPointerException in PaymentProcessor.process() at line 247"})
          for i in range(5)],
        *[json.dumps({"timestamp": _ts(100 - i * 2), "level": "info",
                      "service": "api-gateway", "pod": _PODS["api-gateway"],
                      "message": "Request processed: GET /api/v1/payments 200 OK"})
          for i in range(8)],
    ])

    timeout_spike = "\n".join([
        *[json.dumps({"timestamp": _ts(300 - i * 5), "level": "warning",
                      "service": "order-processor", "pod": _PODS["order-processor"],
                      "message": f"Request timeout after 30s calling inventory-svc /check-stock (req-{4000+i})"})
          for i in range(7)],
        *[json.dumps({"timestamp": _ts(200 - i * 4), "level": "error",
                      "service": "order-processor", "pod": _PODS["order-processor"],
                      "message": "Circuit breaker OPEN: inventory-svc is failing health checks"})
          for i in range(3)],
        *[json.dumps({"timestamp": _ts(100 - i * 2), "level": "info",
                      "service": "api-gateway", "pod": _PODS["api-gateway"],
                      "message": "Health check passed: all upstream services reporting healthy"})
          for i in range(5)],
    ])

    normal = "\n".join([
        json.dumps({"timestamp": _ts(300 - i * 10), "level": "info",
                    "service": svc, "pod": _PODS[svc],
                    "message": f"Service running normally. CPU: {18 + i * 2}%, Memory: {44 + i}%, Latency: {12 + i}ms"})
        for i, svc in enumerate(_SERVICES * 4)
    ])

    complex_incident = "\n".join([
        *[json.dumps({"timestamp": _ts(300 - i * 3), "level": "error",
                      "service": "auth-service", "pod": _PODS["auth-service"],
                      "message": f"JWT validation failed: token signature mismatch for user session {1000+i}"})
          for i in range(11)],
        *[json.dumps({"timestamp": _ts(200 - i * 4), "level": "error",
                      "service": "api-gateway", "pod": _PODS["api-gateway"],
                      "message": f"Upstream timeout from auth-service: request_id=req-{5000+i}"})
          for i in range(6)],
        json.dumps({"timestamp": _ts(100), "level": "error",
                    "service": "auth-service", "pod": _PODS["auth-service"],
                    "message": "CRITICAL: Redis cluster connection lost — all session invalidations failing silently. Manual intervention required immediately."}),
        json.dumps({"timestamp": _ts(90), "level": "error",
                    "service": "payment-svc", "pod": _PODS["payment-svc"],
                    "message": "Cascading failure: auth-service unavailable, blocking all payment transactions pending authorization"}),
        json.dumps({"timestamp": _ts(80), "level": "error",
                    "service": "order-processor", "pod": _PODS["order-processor"],
                    "message": "Cascading failure: unable to verify payment status, all pending orders halted"}),
    ])

    return {
        "error_spike": error_spike,
        "timeout_spike": timeout_spike,
        "normal": normal,
        "complex_incident": complex_incident,
    }


_SCENARIO_DESCRIPTIONS = {
    "error_spike":      "12+ database connection errors in payment-svc (pool exhaustion + NullPointerException)",
    "timeout_spike":    "7+ timeouts in order-processor calling inventory-svc, circuit breaker open",
    "normal":           "All 5 services running with healthy CPU/memory/latency metrics",
    "complex_incident": "Multi-service cascade: Redis failure → auth errors → payment & order blocking",
}


def _parse_lines(log_text: str) -> list:
    records = []
    for line in log_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            level = data.get("level", "info").lower()
            if level not in ("error", "warning", "info", "debug", "timeout"):
                level = "info"
            records.append({
                "timestamp": data.get("timestamp", ""),
                "service":   data.get("service", "unknown"),
                "pod":       data.get("pod", ""),
                "level":     level,
                "message":   data.get("message", line),
                "raw":       line,
            })
        except json.JSONDecodeError:
            level = "info"
            lc = line.lower()
            if "error" in lc or "fail" in lc or "exception" in lc:
                level = "error"
            elif "timeout" in lc:
                level = "timeout"
            elif "warn" in lc:
                level = "warning"
            records.append({"timestamp": "", "service": "unknown", "pod": "",
                             "level": level, "message": line, "raw": line})
    return records


@mcp.tool()
def fetch_sample_logs(scenario: str = "error_spike") -> str:
    """Fetch sample Kubernetes log data for a given incident scenario."""
    samples = _build_samples()
    if scenario not in samples:
        return json.dumps({"error": f"Unknown scenario '{scenario}'.",
                           "available": list(samples.keys())})
    logs = samples[scenario]
    line_count = sum(1 for l in logs.split("\n") if l.strip())
    return json.dumps({"scenario": scenario,
                        "description": _SCENARIO_DESCRIPTIONS[scenario],
                        "log_count": line_count,
                        "logs": logs}, indent=2)


@mcp.tool()
def parse_and_detect_anomalies(log_text: str) -> str:
    """Parse log lines and detect anomalies using threshold-based rules."""
    records = _parse_lines(log_text)
    errors   = [r for r in records if r["level"] == "error"]
    timeouts = [r for r in records if "timeout" in r["message"].lower()]
    freq     = Counter(r["message"] for r in records)
    rare     = [msg for msg, cnt in freq.items() if cnt == 1 and len(msg) > 30]

    alerts = []
    if len(errors) >= 10:
        alerts.append({"type": "ErrorSpike", "count": len(errors),
                        "message": f"{len(errors)} errors >= threshold of 10",
                        "affected_services": sorted({e["service"] for e in errors}),
                        "sample_messages": [e["message"][:120] for e in errors[:3]]})
    if len(timeouts) >= 5:
        alerts.append({"type": "TimeoutSpike", "count": len(timeouts),
                        "message": f"{len(timeouts)} timeouts >= threshold of 5",
                        "affected_services": sorted({t["service"] for t in timeouts})})
    if rare:
        alerts.append({"type": "RareLogPattern", "count": len(rare),
                        "message": f"{len(rare)} unique anomalous log pattern(s) detected",
                        "examples": rare[:3]})

    stats = {"total_logs": len(records), "error_count": len(errors),
             "timeout_count": len(timeouts), "rare_pattern_count": len(rare),
             "affected_services": sorted({r["service"] for r in records}),
             "alert_count": len(alerts), "is_healthy": len(alerts) == 0}

    return json.dumps({"alerts": alerts, "stats": stats}, indent=2)


@mcp.tool()
def semantic_analysis(log_text: str) -> str:
    """Compute novelty scores, anomaly scores, and pattern IDs for log lines."""
    records = _parse_lines(log_text)
    if not records:
        return json.dumps({"error": "No log records found in input."})

    msg_freq = Counter(r["message"] for r in records)
    total    = len(records)

    enriched = []
    for r in records[:20]:
        msg    = r["message"]
        freq   = msg_freq[msg]

        # inverse frequency proxy — rare messages score higher
        novelty = round(1.0 - (freq / total), 3)

        anomaly = 0.0
        lc = msg.lower()
        if r["level"] == "error":
            anomaly += 0.5
        if "timeout" in lc or "fail" in lc:
            anomaly += 0.2
        if "critical" in lc or "cascade" in lc or "circuit breaker" in lc:
            anomaly += 0.3
        anomaly = min(round(anomaly, 2), 1.0)

        pattern_raw = f"{r['service']}.{r['level']}.{msg[:40]}"
        pattern_id  = f"PAT-{hashlib.md5(pattern_raw.encode()).hexdigest()[:8].upper()}"

        enriched.append({"service": r["service"], "level": r["level"],
                          "message_preview": msg[:100],
                          "novelty_score": novelty, "anomaly_score": anomaly,
                          "semantic_confidence": round((novelty + anomaly) / 2, 3),
                          "pattern_id": pattern_id})

    avg_novelty    = round(sum(e["novelty_score"]       for e in enriched) / len(enriched), 3)
    avg_anomaly    = round(sum(e["anomaly_score"]        for e in enriched) / len(enriched), 3)
    avg_confidence = round(sum(e["semantic_confidence"]  for e in enriched) / len(enriched), 3)

    return json.dumps({
        "summary": {"total_analyzed": total, "enriched_sample_size": len(enriched),
                    "avg_novelty_score": avg_novelty, "avg_anomaly_score": avg_anomaly,
                    "avg_semantic_confidence": avg_confidence,
                    "high_anomaly_count": sum(1 for e in enriched if e["anomaly_score"] > 0.5),
                    "novel_log_count": sum(1 for e in enriched if e["novelty_score"] > 0.8)},
        "enriched_logs": enriched,
    }, indent=2)


@mcp.tool()
def correlate_alerts(alerts_json: str) -> str:
    """Correlate detected alerts into a categorized incident with severity."""
    _CATEGORY_MAP = {"ErrorSpike": "application", "TimeoutSpike": "dependency",
                     "RareLogPattern": "anomaly"}
    _SEVERITY_MAP = {
        frozenset({"application", "dependency", "anomaly"}): "critical",
        frozenset({"application", "dependency"}):            "high",
        frozenset({"application", "anomaly"}):               "high",
        frozenset({"dependency", "anomaly"}):                "medium",
        frozenset({"application"}):                          "medium",
        frozenset({"dependency"}):                           "medium",
        frozenset({"anomaly"}):                              "low",
    }

    try:
        data = json.loads(alerts_json)
        alerts = data.get("alerts", data) if isinstance(data, dict) else data
        if not isinstance(alerts, list):
            alerts = []
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"error": "Invalid JSON — pass the output of parse_and_detect_anomalies."})

    categories = {_CATEGORY_MAP.get(a.get("type", ""), "unknown") for a in alerts}
    categories.discard("unknown")

    if not categories:
        return json.dumps({"status": "healthy", "message": "No alerts to correlate."})

    return json.dumps({
        "incident_id": f"INC-{int(time.time())}",
        "categories":  sorted(categories),
        "severity":    _SEVERITY_MAP.get(frozenset(categories), "medium"),
        "alert_count": len(alerts),
        "created_at":  datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "alerts":      alerts,
        "status":      "open",
    }, indent=2)


@mcp.tool()
def root_cause_analysis(incident_json: str) -> str:
    """Rule-based RCA with confidence scores and recommended actions."""
    try:
        incident = json.loads(incident_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON — pass the output of correlate_alerts."})

    categories = incident.get("categories", [])
    causes = []

    if "application" in categories:
        causes.append({"cause": "Application error regression or resource exhaustion",
                        "confidence": 0.75,
                        "evidence": "ErrorSpike: elevated error rate from application-layer exceptions",
                        "recommended_actions": [
                            "Check git log / deployment history for last 24 hours",
                            "Review stack traces for NullPointerException or connection pool errors",
                            "Verify DB connection pool max_connections vs current active connections",
                            "Consider rollback if a recent deployment correlates with error onset"]})
    if "dependency" in categories:
        causes.append({"cause": "Downstream service or infrastructure degradation",
                        "confidence": 0.85,
                        "evidence": "TimeoutSpike: callers consistently timing out on downstream services",
                        "recommended_actions": [
                            "Check health/status pages of all downstream dependencies",
                            "Review circuit breaker states",
                            "Inspect network latency and DNS resolution between pods",
                            "Scale up the dependency service if CPU/memory constrained",
                            "Review and tune timeout + retry policies"]})
    if "anomaly" in categories:
        causes.append({"cause": "Rare or unexpected system behavior (potential security/config event)",
                        "confidence": 0.60,
                        "evidence": "RareLogPattern: log messages not seen during normal operations",
                        "recommended_actions": [
                            "Manually inspect each rare log message for security indicators",
                            "Check for configuration drift",
                            "Alert security team if auth/token-related anomalies are present"]})
    if not causes:
        causes.append({"cause": "Unclassified anomaly", "confidence": 0.40,
                        "evidence": "No alert pattern matched a known category",
                        "recommended_actions": ["Review raw logs manually", "Escalate to on-call engineer"]})

    rca = {"incident_id": incident.get("incident_id", "unknown"),
           "severity": incident.get("severity", "medium"),
           "categories": categories,
           "rule_based_rca": causes,
           "overall_confidence": max(c["confidence"] for c in causes),
           "priority_action": causes[0]["recommended_actions"][0],
           "analyzed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

    try:
        from utils.llm_config import USE_LLM
        if USE_LLM:
            from utils.llm_rca import llm_rca
            rca["llm_rca"] = llm_rca({"incident_id": incident.get("incident_id"),
                                       "categories": categories,
                                       "alerts": incident.get("alerts", [])[:3]})
    except Exception:
        rca["llm_note"] = "Set USE_LLM=true and OPENAI_API_KEY for AI-powered RCA enrichment."

    return json.dumps(rca, indent=2)


@mcp.tool()
def list_incidents(limit: int = 5) -> str:
    """List recently persisted incidents from the data/incidents directory."""
    incidents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "incidents")

    if not os.path.exists(incidents_dir):
        return json.dumps({"message": "No incidents directory found.", "incidents": []})

    files = sorted([f for f in os.listdir(incidents_dir) if f.endswith(".json")],
                   reverse=True)[:max(1, limit)]

    incidents = []
    for fname in files:
        try:
            with open(os.path.join(incidents_dir, fname)) as fh:
                data = json.load(fh)
            ts = data.get("analyzed_at", 0)
            incidents.append({
                "incident_id":    data.get("incident_id", fname.replace(".json", "")),
                "categories":     data.get("categories", []),
                "analyzed_at":    datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else "unknown",
                "cause_count":    len(data.get("rule_based_rca", [])),
                "has_llm_rca":    "llm_rca" in data,
                "priority_cause": (data.get("rule_based_rca") or [{}])[0].get("cause", ""),
            })
        except Exception as exc:
            incidents.append({"file": fname, "error": str(exc)})

    return json.dumps({"total_on_disk": len(os.listdir(incidents_dir)),
                        "returned": len(incidents), "incidents": incidents}, indent=2)


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search historical incidents and runbooks matching the query."""
    # try FAISS RAG first if OPENAI_API_KEY is available
    try:
        from rag.rag_store import retrieve_context
        results = retrieve_context(query, k=3)
        if results:
            return json.dumps({"source": "faiss_rag", "query": query,
                                "results": results if isinstance(results, list) else [{"content": results}]},
                               indent=2)
    except Exception:
        pass

    RUNBOOKS = [
        {"title": "Database Connection Pool Exhaustion",
         "keywords": ["database", "connection", "pool", "jdbc", "postgres", "mysql"],
         "content": ("1. Check current pool utilization.\n2. Increase max_connections.\n"
                     "3. Identify long-running queries.\n4. Consider adding PgBouncer.\n"
                     "5. Review application for connection leaks.")},
        {"title": "Service Timeout & Circuit Breaker",
         "keywords": ["timeout", "circuit breaker", "latency", "slow", "retry"],
         "content": ("1. Check circuit breaker state.\n2. Review downstream SLOs and p99 latency.\n"
                     "3. Add exponential backoff + jitter.\n4. Inspect pod resource limits.\n"
                     "5. Review Kubernetes HPA settings.")},
        {"title": "Authentication / JWT / Session Failures",
         "keywords": ["auth", "jwt", "token", "session", "redis", "oauth"],
         "content": ("1. Verify JWT signing keys across replicas.\n2. Check Redis connectivity.\n"
                     "3. Review token expiry — clock skew > 5min causes rejections.\n"
                     "4. Implement graceful degradation for cached sessions.\n"
                     "5. Audit recent key rotation events.")},
        {"title": "Cascading Failure Containment",
         "keywords": ["cascade", "cascading", "multi-service", "critical", "blocking"],
         "content": ("1. Identify the root failure source.\n2. Isolate failing services.\n"
                     "3. Enable fallback / degraded mode.\n4. Scale up critical path services.\n"
                     "5. Post incident: implement bulkheads and load shedding.")},
    ]

    kw_lower = query.lower().split()
    matched = []
    for rb in RUNBOOKS:
        score = sum(1 for kw in kw_lower if any(kw in rk for rk in rb["keywords"]))
        if score > 0:
            matched.append({"score": score, "title": rb["title"], "content": rb["content"]})
    matched.sort(key=lambda x: x.pop("score"), reverse=True)

    incidents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "incidents")
    historical = []
    if os.path.exists(incidents_dir):
        for fname in os.listdir(incidents_dir):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(incidents_dir, fname)) as fh:
                    data = json.load(fh)
                score = sum(1 for kw in kw_lower if kw in json.dumps(data).lower())
                if score > 0:
                    historical.append({"incident_id": data.get("incident_id", fname),
                                        "categories": data.get("categories", []),
                                        "relevance": score,
                                        "top_cause": (data.get("rule_based_rca") or [{}])[0].get("cause", "")})
            except Exception:
                continue
        historical.sort(key=lambda x: x.pop("relevance"), reverse=True)

    return json.dumps({"source": "keyword_search", "query": query,
                        "runbooks": matched[:2], "historical_matches": historical[:3],
                        "total_results": len(matched) + len(historical)}, indent=2)


TOOL_REGISTRY = {
    "fetch_sample_logs":          {"fn": fetch_sample_logs,
                                   "description": "Fetch sample Kubernetes log data for a given incident scenario.",
                                   "input_schema": {"type": "object", "properties": {"scenario": {"type": "string"}}}},
    "parse_and_detect_anomalies": {"fn": parse_and_detect_anomalies,
                                   "description": "Parse log lines and detect anomalies (ErrorSpike, TimeoutSpike, RareLogPattern).",
                                   "input_schema": {"type": "object", "properties": {"log_text": {"type": "string"}}, "required": ["log_text"]}},
    "semantic_analysis":          {"fn": semantic_analysis,
                                   "description": "Compute novelty scores, anomaly scores, and pattern IDs.",
                                   "input_schema": {"type": "object", "properties": {"log_text": {"type": "string"}}, "required": ["log_text"]}},
    "correlate_alerts":           {"fn": correlate_alerts,
                                   "description": "Correlate detected alerts into a categorized incident with severity.",
                                   "input_schema": {"type": "object", "properties": {"alerts_json": {"type": "string"}}, "required": ["alerts_json"]}},
    "root_cause_analysis":        {"fn": root_cause_analysis,
                                   "description": "Rule-based RCA with confidence scores and remediation actions.",
                                   "input_schema": {"type": "object", "properties": {"incident_json": {"type": "string"}}, "required": ["incident_json"]}},
    "list_incidents":             {"fn": list_incidents,
                                   "description": "List recently persisted incidents.",
                                   "input_schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    "search_knowledge_base":      {"fn": search_knowledge_base,
                                   "description": "Search historical incidents and runbooks matching the query.",
                                   "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
}


if __name__ == "__main__":
    if _HAS_MCP:
        mcp.run()
    else:
        print("mcp package not installed. Use TOOL_REGISTRY directly.")
        print("Available tools:", list(TOOL_REGISTRY.keys()))
