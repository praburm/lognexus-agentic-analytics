from datetime import datetime

def now_str():
    return datetime.now().isoformat(sep=' ', timespec='seconds')


def safe_float(val, default=0.0):
    try:
        return float(val)
    except Exception:
        return default
