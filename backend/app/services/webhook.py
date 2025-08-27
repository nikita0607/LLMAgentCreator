import requests

def call_webhook(url: str, payload: dict):
    print(url, payload)
    r = requests.post(url, json=payload, timeout=5)
    print(url, r)
    return r.json() if r.headers.get("content-type") == "application/json" else r.text