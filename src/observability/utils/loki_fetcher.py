import os
import time
import requests

LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
QUERY = '{namespace="logan"}'
LIMIT = 5000


def fetch_logs(minutes=5):
    end = int(time.time())
    start = end - minutes * 60

    params = {
        "query": QUERY,
        "start": start * 1_000_000_000,
        "end": end * 1_000_000_000,
        "limit": LIMIT,
        "direction": "BACKWARD"
    }

    resp = requests.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params=params,
        timeout=10
    )
    resp.raise_for_status()

    data = resp.json()["data"]["result"]

    logs = []
    for stream in data:
        for timestamp, line in stream.get("values", []):
            logs.append({
                "timestamp": timestamp,
                "stream": stream.get("stream", {}),
                "line": line
            })

    return logs
