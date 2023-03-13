# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for config.py file."""

import os

from wordcab_slack.config import (
    EMOJI_FLAGS_MAP,
    EMOJI_NUMBERS_MAP,
    LANGUAGES,
    SLACK_BOT_TOKEN,
    SLACK_SIGNING_SECRET,
    SUMMARY_TYPES,
    WORDCAB_API_KEY,
)


def test_slack_bot_token():
    """Test the SLACK_BOT_TOKEN constant."""
    assert SLACK_BOT_TOKEN == os.getenv("SLACK_BOT_TOKEN")


def test_slack_signing_secret():
    """Test the SLACK_SIGNING_SECRET constant."""
    assert SLACK_SIGNING_SECRET == os.getenv("SLACK_SIGNING_SECRET")


def test_wordcab_api_key():
    """Test the WORDCAB_API_KEY constant."""
    assert WORDCAB_API_KEY == os.getenv("WORDCAB_API_KEY")


def test_languages():
    """Test the LANGUAGES constant."""
    assert isinstance(LANGUAGES, list)
    assert len(LANGUAGES) > 0
    assert len(LANGUAGES) == 8
    assert LANGUAGES == ["de", "en", "es", "fr", "it", "pt", "nl", "sv"]


def test_emoji_flags_map():
    """Test the EMOJI_FLAGS_MAP constant."""
    assert isinstance(EMOJI_FLAGS_MAP, dict)
    assert len(EMOJI_FLAGS_MAP) > 0
    assert len(EMOJI_FLAGS_MAP) == len(LANGUAGES)
    for lang in LANGUAGES:
        assert lang in EMOJI_FLAGS_MAP
        assert isinstance(EMOJI_FLAGS_MAP[lang], str)


def test_emoji_numbers_map():
    """Test the EMOJI_NUMBERS_MAP constant."""
    assert isinstance(EMOJI_NUMBERS_MAP, dict)
    assert len(EMOJI_NUMBERS_MAP) > 0
    assert len(EMOJI_NUMBERS_MAP) == 10
    assert EMOJI_NUMBERS_MAP[1] == "one"
    assert EMOJI_NUMBERS_MAP[2] == "two"
    assert EMOJI_NUMBERS_MAP[3] == "three"
    assert EMOJI_NUMBERS_MAP[4] == "four"
    assert EMOJI_NUMBERS_MAP[5] == "five"
    assert EMOJI_NUMBERS_MAP[6] == "six"
    assert EMOJI_NUMBERS_MAP[7] == "seven"
    assert EMOJI_NUMBERS_MAP[8] == "eight"
    assert EMOJI_NUMBERS_MAP[9] == "nine"
    assert EMOJI_NUMBERS_MAP[10] == "ten"


def test_summary_types():
    """Test the SUMMARY_TYPES constant."""
    assert isinstance(SUMMARY_TYPES, list)
    assert len(SUMMARY_TYPES) > 0
    assert len(SUMMARY_TYPES) == 4
    assert "brief" in SUMMARY_TYPES
    assert "conversational" in SUMMARY_TYPES
    assert "narrative" in SUMMARY_TYPES
    assert "no_speaker" in SUMMARY_TYPES
