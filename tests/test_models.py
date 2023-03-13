# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for models.py file."""

import pytest

from wordcab_slack.models import JobData


@pytest.fixture
def valid_data():
    """Fixture for valid job."""
    return {
        "summary_length": [100, 200],
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": ["http://example.com"],
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_urls():
    """Fixture for invalid urls."""
    return {
        "summary_length": [100, 200],
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": "example.com",
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_summary_type():
    """Fixture for invalid summary type."""
    return {
        "summary_length": [100, 200],
        "summary_type": "text",
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": ["example.com"],
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_summary_length():
    """Fixture for invalid summary length."""
    return {
        "summary_length": 100,
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": ["example.com"],
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_context_features():
    """Fixture for invalid context features."""
    return {
        "summary_length": [100, 200],
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": [1, 2],
        "urls": ["example.com"],
        "msg_id": "1234",
    }


def test_valid_job_data(valid_data):
    """Test valid job data."""
    job_data = JobData(**valid_data)
    assert job_data.summary_length == [100, 200]
    assert job_data.summary_type == ["text", "audio"]
    assert job_data.source_lang == "en"
    assert job_data.urls == ["http://example.com"]
    assert job_data.msg_id == "1234"
    assert job_data.num_tasks == 2


def test_invalid_urls(invalid_urls):
    """Test invalid urls."""
    with pytest.raises(ValueError):
        JobData(**invalid_urls)


def test_invalid_summary_type(invalid_summary_type):
    """Test invalid summary type."""
    with pytest.raises(ValueError):
        JobData(**invalid_summary_type)


def test_invalid_summary_length(invalid_summary_length):
    """Test invalid summary length."""
    with pytest.raises(ValueError):
        JobData(**invalid_summary_length)
