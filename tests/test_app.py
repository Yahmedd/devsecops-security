import os
import sys

# Ensure cybertek package is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybertek import create_app


def test_home_route_returns_200(tmp_path, monkeypatch):
    # Use a temporary sqlite DB for tests
    db_path = tmp_path / "test_cybertek.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")

    app = create_app('testing')
    client = app.test_client()

    resp = client.get('/')
    assert resp.status_code == 200
