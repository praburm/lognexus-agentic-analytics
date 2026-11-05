import os
import requests
import threading
import time
import signal
import sys

def _urls(env_var):
    val = os.getenv(env_var, "").strip()
    return [u.strip() for u in val.split(",") if u.strip()]

ERROR_URLS   = _urls("ALERT_ERROR_TARGETS")
TIMEOUT_URLS = _urls("ALERT_TIMEOUT_TARGETS")
RARE_URLS    = _urls("ALERT_RARE_TARGETS")
URL_GROUPS   = [g for g in [ERROR_URLS, TIMEOUT_URLS, RARE_URLS] if g]

if not URL_GROUPS:
    print("[ERROR] Set ALERT_ERROR_TARGETS, ALERT_TIMEOUT_TARGETS, and/or ALERT_RARE_TARGETS.")
    sys.exit(1)

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


def generate_cycle_for_urls(urls):
    threads = []
    for _ in range(REQUESTS_PER_URL):
        for url in urls:
            t = threading.Thread(target=hit, args=(url,))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()


group_index = 0

print("🚀 Continuous alert generator started (cycling through alert groups every 30s)")

while running:
    start = time.time()

    current_urls = URL_GROUPS[group_index]
    print(f"⚡ Generating traffic for group {group_index + 1}/{len(URL_GROUPS)}: {current_urls}")

    generate_cycle_for_urls(current_urls)
    print("✅ Cycle complete")

    group_index = (group_index + 1) % len(URL_GROUPS)

    elapsed = time.time() - start
    sleep_time = max(0, CYCLE_INTERVAL - elapsed)
    time.sleep(sleep_time)

