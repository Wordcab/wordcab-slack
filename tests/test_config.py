# Copyright (c) 2023, The Wordcab team. All rights reserved.

try:
    from wordcab_slack.config import (
        EMOJI_FLAGS_MAP,
        EMOJI_NUMBERS_MAP,
        LANGUAGES,
        SLACK_BOT_TOKEN,
        SLACK_SIGNING_SECRET,
        SUMMARY_TYPES,
        WORDCAB_API_KEY,
    )
except ImportError:
    raise ImportError("Please create a .env file in the root directory of the project.")


def test_languages():
    assert isinstance(LANGUAGES, list)
    assert len(LANGUAGES) > 0
    assert len(LANGUAGES) == 7
    assert "de" in LANGUAGES
    assert "en" in LANGUAGES
    assert "es" in LANGUAGES
    assert "fr" in LANGUAGES
    assert "it" in LANGUAGES
    assert "nl" in LANGUAGES
    assert "sv" in LANGUAGES


def test_emoji_flags_map():
    assert isinstance(EMOJI_FLAGS_MAP, dict)
    assert len(EMOJI_FLAGS_MAP) > 0
    assert len(EMOJI_FLAGS_MAP) == len(LANGUAGES)
    for lang in LANGUAGES:
        assert lang in EMOJI_FLAGS_MAP
        assert isinstance(EMOJI_FLAGS_MAP[lang], str)


def test_emoji_numbers_map():
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
    assert isinstance(SUMMARY_TYPES, list)
    assert len(SUMMARY_TYPES) > 0
    assert len(SUMMARY_TYPES) == 4
    assert "narrative" in SUMMARY_TYPES
    assert "conversational" in SUMMARY_TYPES
    assert "no_speaker" in SUMMARY_TYPES
    assert "reason_conclusion" in SUMMARY_TYPES
