from utils.loki_fetcher import fetch_logs
from utils.log_normalizer import normalize
from utils.detector import detect_anomalies


def run_pipeline():
    raw_logs = fetch_logs(minutes=5)
    print(f"Fetched {len(raw_logs)} raw logs")

    logs = normalize(raw_logs)
    print(f"Normalized {len(logs)} logs")

    alerts, stats = detect_anomalies(logs)

    print(f"\n[Detector Summary]")
    print(f"  total logs     = {stats['total']}")
    print(f"  error logs     = {stats['errors']}")
    print(f"  timeout logs   = {stats['timeouts']}")
    print(f"  rare patterns  = {stats['rare']}")
    print(f"  alerts raised  = {len(alerts)}")

    for alert in alerts:
        print("\nALERT:", alert["message"])
        print(alert)


if __name__ == "__main__":
    run_pipeline()
