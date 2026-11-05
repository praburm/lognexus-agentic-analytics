import json


def infer_level(text):
    text = text.lower()
    if "error" in text or "fail" in text or "exception" in text:
        return "error"
    if "timeout" in text:
        return "timeout"
    if "warn" in text:
        return "warning"
    return "info"


def normalize(records):
    normalized = []

    for rec in records:
        timestamp = rec.get("timestamp")
        labels = rec.get("stream", {})
        raw = rec.get("line", "").strip()

        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {}

        message = parsed.get("msg") or parsed.get("message") or raw
        level = (parsed.get("level") or parsed.get("severity") or infer_level(raw)).lower()

        normalized.append({
            "timestamp": timestamp,
            "service": labels.get("app") or labels.get("job") or "",
            "pod": labels.get("pod") or "",
            "level": level,
            "message": message,
            "raw": raw,
        })

    return normalized
