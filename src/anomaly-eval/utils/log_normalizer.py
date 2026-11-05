def infer_level(text):
    text = text.lower()
    if "error" in text or "exception" in text or "fail" in text:
        return "error"
    if "warn" in text:
        return "warning"
    return "info"


def normalize(records):
    return [
        {"level": infer_level(rec.get("line", "")), "message": rec.get("line", "").strip()}
        for rec in records
    ]
