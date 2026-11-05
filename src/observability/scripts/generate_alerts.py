import os
import requests
import threading
import time
import signal
import sys

_targets = os.getenv("ALERT_TARGETS", "").strip()
if not _targets:
    print("[ERROR] Set ALERT_TARGETS as a comma-separated list of endpoint URLs.")
    sys.exit(1)

URLS = [u.strip() for u in _targets.split(",") if u.strip()]

REQUESTS_PER_URL = 10        # per cycle
CYCLE_INTERVAL = 30          # seconds
REQUEST_TIMEOUT = 2

running = True


def signal_handler(sig, frame):
    global running
    print("\n🛑 Stopping alert generator...")
    running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def hit(url):
    try:
        requests.get(url, timeout=REQUEST_TIMEOUT)
    except Exception:
        pass


def generate_cycle():
    threads = []
    for _ in range(REQUESTS_PER_URL):
        for url in URLS:
            t = threading.Thread(target=hit, args=(url,))
            t.start()
            threads.append(t)

    for t in threads:
        t.join()


print("🚀 Continuous alert generator started (every 30s)")

while running:
    start = time.time()

    print("⚡ Generating traffic...")
    generate_cycle()
    print("✅ Cycle complete")

    elapsed = time.time() - start
    sleep_time = max(0, CYCLE_INTERVAL - elapsed)
    time.sleep(sleep_time)

