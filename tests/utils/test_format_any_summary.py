# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _format_any_summary function in utils.py file."""

import io
from typing import Any, Dict, List

import pytest
from wordcab.core_objects import StructuredSummary

from wordcab_slack.utils import _format_any_summary


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "structured_summary, expected",
    [
        (
            [
                StructuredSummary(summary="Summary 1"),
                StructuredSummary(summary="Summary 2"),
            ],
            "Summary 1 Summary 2",
        ),
        ([StructuredSummary(summary="Summary")], "Summary"),
        ([], ""),
    ],
)
async def test__format_any_summary(
    structured_summary: List[Dict[str, Any]], expected: str
) -> None:
    """Test the _format_any_summary function with valid input."""
    result = await _format_any_summary(structured_summary)
    assert isinstance(result, io.StringIO)
    assert result.getvalue() == expected
