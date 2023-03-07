# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the extract_info function in utils.py file."""


from typing import Dict, List, Tuple

import pytest

from wordcab_slack.utils import extract_info


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body, expected_output",
    [
        (
            {
                "event": {
                    "text": "Hello world",
                    "files": [
                        {"url_private_download": "https://example.com/file1.txt"},
                        {"url_private_download": "https://example.com/file2.txt"},
                    ],
                    "channel": "test-channel",
                    "ts": "1234567890.123456",
                }
            },
            (
                "Hello world",
                ["https://example.com/file1.txt", "https://example.com/file2.txt"],
                "test-channel",
                "1234567890.123456",
            ),
        ),
        (
            {
                "event": {
                    "text": "",
                    "files": [],
                    "channel": "test-channel",
                    "ts": "9876543210.987654",
                }
            },
            ("", [], "test-channel", "9876543210.987654"),
        ),
    ],
)
async def test_extract_info(
    body: Dict[str, Dict[str, str]], expected_output: Tuple[str, List[str], str, str]
) -> None:
    """Test the extract_info function with valid input."""
    assert await extract_info(body) == expected_output


@pytest.mark.asyncio
async def test_extract_info_invalid() -> None:
    """Test the extract_info function with invalid input."""
    with pytest.raises(KeyError):
        await extract_info({"event": {}})
    with pytest.raises(KeyError):
        await extract_info({})
