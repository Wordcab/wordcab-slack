# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for main.py file."""

import pytest
from fastapi.testclient import TestClient

from wordcab_slack.main import api


@pytest.fixture
def client():
    """Client fixture for testing."""
    with TestClient(api) as client:
        yield client


def test_health(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_slack_events(client):
    """Test slack events endpoint."""
    response = client.post("/slack/events")
    assert response.status_code == 401
