import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

def test_health():
    client = app.test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert b"healthy" in r.data

def test_index():
    client = app.test_client()
    r = client.get("/")
    assert r.status_code == 200
    assert b"url-health-monitor" in r.data

def test_status():
    client = app.test_client()
    r = client.get("/status")
    assert r.status_code == 200
