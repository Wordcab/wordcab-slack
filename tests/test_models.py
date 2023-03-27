# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for models.py file."""

import pytest

from wordcab_slack.models import JobData


@pytest.fixture
def valid_data_url():
    """Fixture for valid job."""
    return {
        "summary_length": [100, 200],
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": ["http://example.com"],
        "transcript_ids": None,
        "msg_id": "1234",
    }


@pytest.fixture
def valid_data_transcript_id():
    """Fixture for valid job."""
    return {
        "summary_length": [100, 200],
        "summary_type": ["narrative"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": None,
        "transcript_ids": ["1234", "5678", "9012"],
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_data():
    """Fixture for invalid job."""
    return {
        "summary_length": [100, 200],
        "summary_type": ["no_speaker"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": None,
        "transcript_ids": None,
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_urls():
    """Fixture for invalid urls."""
    return {
        "summary_length": [100, 200],
        "summary_type": ["no_speaker"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": "example.com",
        "transcript_ids": None,
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
        "transcript_ids": None,
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_summary_length():
    """Fixture for invalid summary length."""
    return {
        "summary_length": 100,
        "summary_type": ["conversational"],
        "source_lang": "en",
        "target_lang": "en",
        "context_features": ["issue", "purpose"],
        "urls": ["example.com"],
        "transcript_ids": None,
        "msg_id": "1234",
    }


def test_valid_job_data(valid_data_url):
    """Test valid job data."""
    valid_data_url = JobData(**valid_data_url)
    assert valid_data_url.summary_length == [100, 200]
    assert valid_data_url.summary_type == ["text", "audio"]
    assert valid_data_url.source_lang == "en"
    assert valid_data_url.urls == ["http://example.com"]
    assert valid_data_url.transcript_ids is None
    assert valid_data_url.msg_id == "1234"
    assert valid_data_url.num_tasks == 2


def test_valid_job_data_transcript_id(valid_data_transcript_id):
    """Test valid job data."""
    valid_data_transcript_id = JobData(**valid_data_transcript_id)
    assert valid_data_transcript_id.summary_length == [100, 200]
    assert valid_data_transcript_id.summary_type == ["narrative"]
    assert valid_data_transcript_id.source_lang == "en"
    assert valid_data_transcript_id.urls is None
    assert valid_data_transcript_id.transcript_ids == ["1234", "5678", "9012"]
    assert valid_data_transcript_id.msg_id == "1234"
    assert valid_data_transcript_id.num_tasks == 3


def test_invalid_job_data(invalid_data):
    """Test invalid job data."""
    with pytest.raises(ValueError):
        JobData(**invalid_data)


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
