# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _format_brief_summary function in utils.py file."""

import io
from typing import Any, Dict, List

import pytest
from wordcab.core_objects import StructuredSummary

from wordcab_slack.utils import _format_brief_summary


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "structured_summary, expected",
    [
        (
            [
                StructuredSummary(
                    summary={"title": "Title 1", "brief_summary": "Summary 1"}
                ),
                StructuredSummary(
                    summary={"title": "Title 2", "brief_summary": "Summary 2"}
                ),
            ],
            "Title: Title 1\nBrief summary: Summary 1\n\nTitle: Title 2\nBrief summary: Summary 2",
        ),
        (
            [StructuredSummary(summary={"title": "Title", "brief_summary": "Summary"})],
            "Title: Title\nBrief summary: Summary",
        ),
        ([], ""),
    ],
)
async def test__format_brief_summary(
    structured_summary: List[Dict[str, Any]], expected: str
) -> None:
    """Test the _format_brief_summary function with valid input."""
    result = await _format_brief_summary(structured_summary)
    assert isinstance(result, io.StringIO)
    assert result.getvalue() == expected
