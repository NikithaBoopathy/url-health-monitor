import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app as flask_app

def test_health():
    client = flask_app.test_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert b"healthy" in r.data

def test_index():
    client = flask_app.test_client()
    r = client.get("/")
    assert r.status_code == 200
    assert b"url-health-monitor" in r.data

def test_status():
    client = flask_app.test_client()
    r = client.get("/status")
    assert r.status_code == 200
