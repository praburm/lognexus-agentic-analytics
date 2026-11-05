from collections import Counter

ERROR_THRESHOLD = 10
TIMEOUT_THRESHOLD = 5
RARE_PATTERN_MIN_LENGTH = 30


def detect_anomalies(logs):
    errors = [log for log in logs if log["level"] == "error"]
    timeouts = [log for log in logs if "timeout" in log.get("message", "").lower()]

    freq = Counter(l["message"] for l in logs)
    rare_logs = [
        msg for msg, count in freq.items()
        if count == 1 and len(msg) > RARE_PATTERN_MIN_LENGTH
    ]

    alerts = []

    if len(errors) >= ERROR_THRESHOLD:
        alerts.append({
            "type": "ErrorSpike",
            "count": len(errors),
            "message": f"{len(errors)} errors >= {ERROR_THRESHOLD}",
        })

    if len(timeouts) >= TIMEOUT_THRESHOLD:
        alerts.append({
            "type": "TimeoutSpike",
            "count": len(timeouts),
            "message": f"{len(timeouts)} timeouts >= {TIMEOUT_THRESHOLD}",
        })

    if rare_logs:
        alerts.append({
            "type": "RareLogPattern",
            "count": len(rare_logs),
            "example": rare_logs[:3],
            "message": f"{len(rare_logs)} rare log patterns detected",
        })

    stats = {
        "total": len(logs),
        "errors": len(errors),
        "timeouts": len(timeouts),
        "rare": len(rare_logs),
    }

    return alerts, stats
