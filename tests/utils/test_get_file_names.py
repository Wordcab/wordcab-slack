# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _get_file_names function in utils.py file."""

import pytest
from typing import List

from wordcab_slack.utils import _get_file_names


@pytest.fixture
def urls():
    """Return a list of urls for testing."""
    return ["https://example.com/test1.pdf", "https://example.com/test2.pdf"]


@pytest.mark.asyncio
async def test_single_url():
    """Test the _get_file_names function with a single url."""
    urls = ["https://example.com/test.pdf"]
    expected = ["test.pdf"]
    result = await _get_file_names(urls)
    assert result == expected


@pytest.mark.asyncio
async def test_multiple_urls(urls):
    """Test the _get_file_names function with multiple urls."""
    expected = ["test1.pdf", "test2.pdf"]
    result = await _get_file_names(urls)
    assert result == expected


@pytest.mark.asyncio
async def test_empty_list():
    """Test the _get_file_names function with an empty list."""
    urls: List[str] = []
    expected: List[str] = []
    result = await _get_file_names(urls)
    assert result == expected
