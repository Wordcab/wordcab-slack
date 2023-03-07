# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _check_file_extension function in utils.py file."""

from typing import List

import pytest
from wordcab.config import AVAILABLE_AUDIO_FORMATS, AVAILABLE_GENERIC_FORMATS

from wordcab_slack.utils import _check_file_extension


@pytest.fixture
def accepted_audio_formats() -> List[str]:
    """Return the list of accepted audio formats."""
    return AVAILABLE_AUDIO_FORMATS


@pytest.fixture
def accepted_generic_formats() -> List[str]:
    """Return the list of accepted generic formats."""
    return AVAILABLE_GENERIC_FORMATS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename, expected",
    [
        ("audio.wav", "audio"),
        ("audio.mp3", "audio"),
        ("document.txt", "generic"),
        ("document.json", "generic"),
        ("document.pdf", ".pdf"),
        ("image.png", ".png"),
    ],
)
async def test_check_file_extension(
    filename, expected, accepted_audio_formats, accepted_generic_formats
):
    """Test the _check_file_extension function with valid input."""
    assert (
        await _check_file_extension(
            filename, accepted_audio_formats, accepted_generic_formats
        )
        == expected
    )


@pytest.mark.asyncio
async def test_check_file_extension_unknown_extension(
    accepted_audio_formats, accepted_generic_formats
):
    """Test the _check_file_extension function with unknown extension."""
    assert (
        await _check_file_extension(
            "unknown.xyz", accepted_audio_formats, accepted_generic_formats
        )
        == ".xyz"
    )
