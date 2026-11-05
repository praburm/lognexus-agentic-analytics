from utils.llm_config import USE_LLM
from utils.utils import safe_float

client = None
if USE_LLM:
    try:
        from openai import OpenAI
        client = OpenAI()
    except Exception:
        client = None


def enrich_logs(logs, use_llm=False):
    enriched = []
    novelty_scores = []
    anomaly_scores = []
    semantic_confidences = []

    for log in logs:
        entry = dict(log)  # copy to avoid mutating the original

        entry["message"] = log.get("message", "")
        entry["level"] = log.get("level", "info")
        entry["service"] = log.get("service", "")
        entry["timestamp"] = log.get("timestamp")

        try:
            entry["embedding_vector"] = _get_embedding(entry["message"])
        except Exception:
            entry["embedding_vector"] = []

        try:
            if use_llm:
                entry["llm_anomaly_estimate"] = _estimate_anomaly(entry)
            else:
                entry["llm_anomaly_estimate"] = {"anomaly_score": 0.0, "baseline_deviation": 1.0}
        except Exception:
            entry["llm_anomaly_estimate"] = {"anomaly_score": 0.3, "baseline_deviation": 1.0}

        try:
            entry["novelty_score"] = _estimate_novelty(entry)
        except Exception:
            entry["novelty_score"] = 0.3

        entry["is_novel"] = entry["novelty_score"] > 0.8

        try:
            entry["pattern_id"] = _pattern_id(entry)
        except Exception:
            entry["pattern_id"] = "unknown.pattern"

        try:
            entry["semantic_confidence"] = _semantic_confidence(entry)
        except Exception:
            entry["semantic_confidence"] = 0.3

        novelty_scores.append(entry["novelty_score"])
        anomaly_scores.append(safe_float(entry["llm_anomaly_estimate"].get("anomaly_score", 0.3)))
        semantic_confidences.append(entry["semantic_confidence"])
        enriched.append(entry)

    metrics = {}

    if enriched:
        total = len(enriched)
        novel_count = sum(1 for n in novelty_scores if n > 0.8)
        avg_novelty = sum(novelty_scores) / total
        avg_anomaly = sum(anomaly_scores) / total
        avg_conf = sum(semantic_confidences) / total

        metrics = {
            "Total events": total,
            "Avg novelty score": round(avg_novelty, 2),
            "Novel events": f"{novel_count}/{total}",
            "Avg anomaly score": round(avg_anomaly, 2),
            "Avg semantic conf": round(avg_conf, 2),
            "LLM anomaly enabled": bool(use_llm),
        }

        print("\nML METRICS")
        print("+----------------------+----------------+")
        print("| Metric               | Value          |")
        print("+----------------------+----------------+")
        print(f"| Total events         | {total:<14} |")
        print(f"| Avg novelty score    | {avg_novelty:<14.2f} |")
        print(f"| Novel events         | {novel_count}/{total:<11} |")
        print(f"| Avg anomaly score    | {avg_anomaly:<14.2f} |")
        print(f"| Avg semantic conf    | {avg_conf:<14.2f} |")
        print(f"| LLM anomaly enabled  | {str(use_llm):<14} |")
        print("+----------------------+----------------+\n")

    return enriched, metrics


def _get_embedding(text):
    if not client:
        return []
    try:
        resp = client.embeddings.create(model="text-embedding-3-large", input=text)
        return resp.data[0].embedding
    except Exception:
        return []


def _estimate_anomaly(log):
    if not client:
        return {"anomaly_score": 0.3, "baseline_deviation": 1.0}
    prompt = f"Log message:\n{log['message']}\n\nEstimate anomaly_score (0-1) and baseline_deviation.\nReturn JSON only."
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return eval(resp.choices[0].message.content)
    except Exception:
        return {"anomaly_score": 0.4, "baseline_deviation": 1.2}


def _estimate_novelty(log):
    return min(1.0, len(log.get("message", "")) / 120)


def _pattern_id(log):
    svc = log.get("service", "unknown")
    lvl = log.get("level", "info")
    key = log.get("message", "")[:40]
    return f"{svc}.{lvl}.{abs(hash(key)) % 1000}"


def _semantic_confidence(log):
    a = safe_float(log.get("llm_anomaly_estimate", {}).get("anomaly_score", 0.3))
    n = safe_float(log.get("novelty_score", 0.3))
    return round(min(1.0, (a + n) / 2), 2)
