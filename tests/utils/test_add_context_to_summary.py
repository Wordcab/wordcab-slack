# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _add_context_to_summary function in utils.py file."""

import io
from typing import Dict, List, Union

import pytest

from wordcab_slack.utils import _add_context_to_summary


@pytest.fixture
def summary() -> io.StringIO:
    """Return the summary."""
    return io.StringIO("initial summary")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "context, expected",
    [
        (
            {
                "key1": "value1",
                "key2": ["value2a", "value2b"],
                "key3": {"key4": "value4"},
            },
            "initial summary\n\nkey1: value1\n\nkey2: ['value2a', 'value2b']\n\nkey3: {'key4': 'value4'}",
        ),
        ({"key": "value"}, "initial summary\n\nkey: value"),
        ({}, "initial summary"),
    ],
)
async def test_add_context_to_summary(
    summary: io.StringIO,
    context: Dict[str, Union[str, List[str], Dict[str, Union[str, List[str]]]]],
    expected: str,
) -> None:
    """Test the _add_context_to_summary function with valid input."""
    result = await _add_context_to_summary(summary, context)
    assert result.getvalue() == expected
