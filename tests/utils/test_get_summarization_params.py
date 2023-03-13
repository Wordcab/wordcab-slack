# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the get_summarization_params function in utils.py file."""

from typing import List

import pytest

from wordcab_slack.config import SUMMARY_TYPES
from wordcab_slack.utils import get_summarization_params


@pytest.fixture
def available_summary_types() -> List[str]:
    """Return a list of available summary types for testing."""
    return SUMMARY_TYPES


@pytest.mark.asyncio
async def test_no_params(available_summary_types) -> None:
    """Test the get_summarization_params function with no params."""
    text = "Get me a summary"
    expected = ([1, 3, 5], ["narrative"], "en", "en", None)
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_summary_length(available_summary_types) -> None:
    """Test the get_summarization_params function with summary length params."""
    text = "3 and 4"
    expected = ([3, 4], ["narrative"], "en", "en", None)
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_summary_type(available_summary_types) -> None:
    """Test the get_summarization_params function with summary type params."""
    text = "conversational"
    expected = ([1, 3, 5], ["conversational"], "en", "en", None)
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_source_lang(available_summary_types) -> None:
    """Test the get_summarization_params function with source language params."""
    text = "source_lang:fr"
    expected = ([1, 3, 5], ["narrative"], "fr", "fr", None)
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_different_source_target_lang(available_summary_types) -> None:
    """Test the get_summarization_params function with multiple source language params."""
    text = "source_lang:fr target_lang:de"
    expected = ([1, 3, 5], ["narrative"], "fr", "de", None)
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_context_with_one_feature(available_summary_types) -> None:
    """Test the get_summarization_params function with delete job params."""
    text = "context:issue"
    expected = ([1, 3, 5], ["narrative"], "en", "en", ["issue"])
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_context_with_multiple_features(available_summary_types) -> None:
    """Test the get_summarization_params function with multiple delete job params."""
    text = "context:issue,purpose,next_steps"
    expected = (
        [1, 3, 5],
        ["narrative"],
        "en",
        "en",
        ["issue", "purpose", "next_steps"],
    )
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_multiple_params(available_summary_types) -> None:
    """Test the get_summarization_params function with multiple params."""
    text = "3 no_speaker source_lang:de target_lang:en context:issue,purpose,next_steps"
    expected = ([3], ["no_speaker"], "de", "en", ["issue", "purpose", "next_steps"])
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_with_only_user_mentions(available_summary_types) -> None:
    """Test the get_summarization_params function with only user mentions."""
    text = "<@U01A1B2C3D>"
    expected = ([1, 3, 5], ["narrative"], "en", "en", None)
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected


@pytest.mark.asyncio
async def test_with_user_mentions_and_params(available_summary_types) -> None:
    """Test the get_summarization_params function with user mentions."""
    text = "<@U01A1B2C3D> 3 no_speaker source_lang:de"
    expected = ([3], ["no_speaker"], "de", "de", None)
    result = await get_summarization_params(text, available_summary_types)
    assert result == expected
