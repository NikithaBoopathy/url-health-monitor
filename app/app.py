from flask import Flask, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)

# URLs to monitor — loaded from env (ConfigMap in K8s)
URLS = os.getenv("URLS_TO_MONITOR", "https://google.com,https://github.com").split(",")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

# In-memory store
status_store = {}

def check_url(url):
    try:
        start = time.time()
        r = requests.get(url, timeout=5)
        elapsed = round((time.time() - start) * 1000)
        status_store[url] = {
            "status": "UP",
            "status_code": r.status_code,
            "response_time_ms": elapsed,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        status_store[url] = {
            "status": "DOWN",
            "error": str(e),
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

def monitor_loop():
    while True:
        for url in URLS:
            check_url(url)
        time.sleep(CHECK_INTERVAL)

# Start background monitoring thread
thread = threading.Thread(target=monitor_loop, daemon=True)
thread.start()

@app.route("/")
def index():
    return jsonify({"service": "url-health-monitor", "version": "1.0"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/status")
def status():
    return jsonify(status_store)

@app.route("/status/<path:url>")
def status_single(url):
    full_url = "https://" + url
    return jsonify(status_store.get(full_url, {"error": "URL not monitored"}))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
