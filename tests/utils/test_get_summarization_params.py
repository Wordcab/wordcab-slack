# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the get_summarization_params function in utils.py file."""

import pytest

from wordcab_slack.utils import get_summarization_params
from wordcab_slack.config import LANGUAGES, SUMMARY_TYPES


@pytest.fixture
def available_summary_types():
    """Return a list of available summary types for testing."""
    return SUMMARY_TYPES


@pytest.fixture
def available_languages():
    """Return a list of available languages for testing."""
    return LANGUAGES


@pytest.mark.asyncio
async def test_no_params(available_summary_types, available_languages):
    """Test the get_summarization_params function with no params."""
    text = "Get me a summary"
    expected = ([1, 3, 5], ["narrative"], "en", True)
    result = await get_summarization_params(text, available_summary_types, available_languages)
    assert result == expected


@pytest.mark.asyncio
async def test_summary_length(available_summary_types, available_languages):
    """Test the get_summarization_params function with summary length params."""
    text = "3 and 4"
    expected = ([3, 4], ["narrative"], "en", True)
    result = await get_summarization_params(text, available_summary_types, available_languages)
    assert result == expected


@pytest.mark.asyncio
async def test_summary_type(available_summary_types, available_languages):
    """Test the get_summarization_params function with summary type params."""
    text = "conversational"
    expected = ([1, 3, 5], ["conversational"], "en", True)
    result = await get_summarization_params(text, available_summary_types, available_languages)
    assert result == expected


@pytest.mark.asyncio
async def test_source_lang(available_summary_types, available_languages):
    """Test the get_summarization_params function with source language params."""
    text = "fr"
    expected = ([1, 3, 5], ["narrative"], "fr", True)
    result = await get_summarization_params(text, available_summary_types, available_languages)
    assert result == expected


@pytest.mark.asyncio
async def test_delete_job(available_summary_types, available_languages):
    """Test the get_summarization_params function with delete job params."""
    text = "False"
    expected = ([1, 3, 5], ["narrative"], "en", False)
    result = await get_summarization_params(text, available_summary_types, available_languages)
    assert result == expected


@pytest.mark.asyncio
async def test_multiple_params(available_summary_types, available_languages):
    """Test the get_summarization_params function with multiple params."""
    text = "3 no_speaker de False"
    expected = ([3], ["no_speaker"], "de", False)
    result = await get_summarization_params(text, available_summary_types, available_languages)
    assert result == expected
