# Copyright (c) 2023, The Wordcab team. All rights reserved.

import pytest

from wordcab_slack.models import JobData


@pytest.fixture
def valid_data():
    return {
        "summary_length": [100, 200],
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "delete_job": False,
        "urls": ["http://example.com"],
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_urls():
    return {
        "summary_length": [100, 200],
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "delete_job": False,
        "urls": "example.com",
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_summary_type():
    return {
        "summary_length": [100, 200],
        "summary_type": "text",
        "source_lang": "en",
        "delete_job": False,
        "urls": ["example.com"],
        "msg_id": "1234",
    }


@pytest.fixture
def invalid_summary_length():
    return {
        "summary_length": 100,
        "summary_type": ["text", "audio"],
        "source_lang": "en",
        "delete_job": False,
        "urls": ["example.com"],
        "msg_id": "1234",
    }


def test_valid_job_data(valid_data):
    job_data = JobData(**valid_data)
    assert job_data.summary_length == [100, 200]
    assert job_data.summary_type == ["text", "audio"]
    assert job_data.source_lang == "en"
    assert job_data.delete_job == False
    assert job_data.urls == ["http://example.com"]
    assert job_data.msg_id == "1234"
    assert job_data.num_tasks == 2


def test_invalid_urls(invalid_urls):
    with pytest.raises(ValueError):
        JobData(**invalid_urls)


def test_invalid_summary_type(invalid_summary_type):
    with pytest.raises(ValueError):
        JobData(**invalid_summary_type)


def test_invalid_summary_length(invalid_summary_length):
    with pytest.raises(ValueError):
        JobData(**invalid_summary_length)
