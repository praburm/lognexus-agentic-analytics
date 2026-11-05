import requests
import json
import os

PUSHOVER_API = "https://api.pushover.net/1/messages.json"

USER_KEY = os.getenv("PUSHOVER_USER_KEY")
APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")


def send_push(rca_result):
    if not USER_KEY or not APP_TOKEN:
        print("Pushover not configured (missing env vars)")
        return

    title = f"RCA Alert: {rca_result.get('incident_id')}"
    message = json.dumps(rca_result, indent=2)[:1000]  # truncate to Pushover's 1024-char limit

    payload = {
        "token": APP_TOKEN,
        "user": USER_KEY,
        "title": title,
        "message": message,
        "priority": 0,
    }

    try:
        response = requests.post(PUSHOVER_API, data=payload, timeout=5)
        if response.status_code != 200:
            print("Pushover error:", response.text)
    except Exception as e:
        print("Failed to send Pushover notification:", e)
