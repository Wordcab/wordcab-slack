# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _get_file_names function in utils.py file."""

import pytest

from wordcab_slack.models import JobData
from wordcab_slack.utils import _get_file_names


@pytest.fixture
def job_data_urls():
    """Return a list of urls for testing."""
    return JobData(
        summary_length=[1, 3],
        summary_type=["conversational"],
        source_lang="en",
        target_lang="en",
        context_features=None,
        urls=["https://example.com/test1.pdf", "https://example.com/test2.pdf"],
        transcript_ids=None,
        msg_id="12345",
        num_tasks=2,
    )


@pytest.fixture
def job_data_transcript_ids():
    """Return a list of transcript_ids for testing."""
    return JobData(
        summary_length=[1, 3],
        summary_type=["conversational"],
        source_lang="en",
        target_lang="en",
        context_features=None,
        urls=None,
        transcript_ids=["12345", "67890"],
        msg_id="12345",
        num_tasks=2,
    )


@pytest.mark.asyncio
async def test_single_url(job_data_urls: JobData):
    """Test for a single url."""
    expected = ["test1.pdf", "test2.pdf"]
    actual = await _get_file_names(job_data_urls)
    assert actual == expected


@pytest.mark.asyncio
async def test_single_transcript_id(job_data_transcript_ids: JobData):
    """Test for a single transcript_id."""
    expected = ["12345", "67890"]
    actual = await _get_file_names(job_data_transcript_ids)
    assert actual == expected
