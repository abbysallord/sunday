"""Tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient

from sunday.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoints:
    def test_basic_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "SUNDAY"

    def test_detailed_health(self, client):
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "subsystems" in data
        assert "llm" in data["subsystems"]
