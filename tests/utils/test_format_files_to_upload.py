# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the format_files_to_upload function in utils.py file."""

import pytest
from wordcab.core_objects import BaseSummary, StructuredSummary

from wordcab_slack.utils import format_files_to_upload


@pytest.fixture
def any_summary():
    """Return a BaseSummary object for testing."""
    items = [
        {"summary": "Lorem ipsum dolor sit amet."},
        {"summary": "Consectetur adipiscing elit."},
    ]
    return BaseSummary(
        job_status="completed",
        summary_id="123",
        summary={
            "key": {"structured_summary": [StructuredSummary(**item) for item in items]}
        },
        summary_type="narrative",
    )


@pytest.fixture
def brief_summary():
    """Return a BaseSummary object for testing."""
    items = [
        {
            "title": "Title 1",
            "brief_summary": "Lorem ipsum dolor sit amet. Consectetur adipiscing elit.",
        },
        {
            "title": "Title 2",
            "brief_summary": "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        },
    ]
    return BaseSummary(
        job_status="completed",
        summary_id="123",
        summary={
            "key": {"structured_summary": [StructuredSummary(**item) for item in items]}
        },
        summary_type="brief",
    )


@pytest.mark.asyncio
async def test_any_summary_type(any_summary):
    """Test the format_files_to_upload function with a summary of type narrative."""
    result = await format_files_to_upload(any_summary)
    assert result[0]["filename"] == "narrative_key_123.txt"
    assert (
        result[0]["file"].getvalue()
        == "Lorem ipsum dolor sit amet. Consectetur adipiscing elit."
    )
    assert result[0]["title"] == "narrative_key_123"
    assert (
        result[0]["alt_text"] == "Summary 123 of type narrative with a length of key."
    )
    assert result[0]["snippet_type"] == "text"


@pytest.mark.asyncio
async def test_multiple_summaries():
    """Test the format_files_to_upload function with multiple summaries."""
    summary = BaseSummary(
        job_status="completed",
        summary_id="123",
        summary={
            "key1": {
                "structured_summary": [
                    StructuredSummary(**{"summary": "Lorem ipsum dolor sit amet."})
                ]
            },
            "key2": {
                "structured_summary": [
                    StructuredSummary(**{"summary": "Consectetur adipiscing elit."})
                ]
            },
        },
        summary_type="narrative",
    )
    result = await format_files_to_upload(summary)
    assert len(result) == 2

    assert result[0]["filename"] == "narrative_key1_123.txt"
    assert result[0]["file"].getvalue() == "Lorem ipsum dolor sit amet."
    assert result[0]["title"] == "narrative_key1_123"
    assert (
        result[0]["alt_text"] == "Summary 123 of type narrative with a length of key1."
    )
    assert result[0]["snippet_type"] == "text"

    assert result[1]["filename"] == "narrative_key2_123.txt"
    assert result[1]["file"].getvalue() == "Consectetur adipiscing elit."
    assert result[1]["title"] == "narrative_key2_123"
    assert (
        result[1]["alt_text"] == "Summary 123 of type narrative with a length of key2."
    )
    assert result[1]["snippet_type"] == "text"
