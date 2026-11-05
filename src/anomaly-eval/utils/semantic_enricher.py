def enrich_logs(logs):
    enriched = []
    for log in logs:
        entry = dict(log)
        novelty_score = min(1.0, len(entry.get("message", "")) / 120)
        entry["novelty_score"] = novelty_score
        entry["is_novel"] = novelty_score > 0.8
        enriched.append(entry)
    return enriched
