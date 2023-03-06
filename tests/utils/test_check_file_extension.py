# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _check_file_extension function in utils.py file"""

import pytest

from typing import List

from wordcab.config import AVAILABLE_AUDIO_FORMATS, AVAILABLE_GENERIC_FORMATS

from wordcab_slack.utils import _check_file_extension


@pytest.fixture
def accepted_audio_formats() -> List[str]:
    return AVAILABLE_AUDIO_FORMATS


@pytest.fixture
def accepted_generic_formats() -> List[str]:
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
        ("image.png", ".png")
    ]
)
async def test_check_file_extension(filename, expected, accepted_audio_formats, accepted_generic_formats):
    assert await _check_file_extension(filename, accepted_audio_formats, accepted_generic_formats) == expected


@pytest.mark.asyncio
async def test_check_file_extension_unknown_extension(accepted_audio_formats, accepted_generic_formats):
    assert await _check_file_extension("unknown.xyz", accepted_audio_formats, accepted_generic_formats) == ".xyz"
