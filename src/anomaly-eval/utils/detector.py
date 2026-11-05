from collections import Counter

ERROR_THRESHOLD = 5
RARE_PATTERN_THRESHOLD = 5
RARE_PATTERN_MIN_LENGTH = 40


def detect_anomalies(logs):
    errors = [log for log in logs if log["level"] == "error"]

    freq = Counter(l["message"] for l in logs)
    rare_logs = [
        msg for msg, count in freq.items()
        if count == 1 and len(msg) > RARE_PATTERN_MIN_LENGTH
    ]

    alerts = []
    if len(errors) >= ERROR_THRESHOLD:
        alerts.append("ErrorSpike")
    if len(rare_logs) >= RARE_PATTERN_THRESHOLD:
        alerts.append("RarePattern")

    return 1 if alerts else 0
