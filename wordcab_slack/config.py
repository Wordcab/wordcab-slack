# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Configuration file for the wordcab_slack package."""

import os

from dotenv import load_dotenv


load_dotenv()

EMOJI_FLAGS_MAP = {
    "de": "flag-de",
    "en": "flag-us",
    "es": "flag-es",
    "fr": "flag-fr",
    "it": "flag-it",
    "pt": "flag-pt",
    "nl": "flag-nl",
    "sv": "flag-se",
}
EMOJI_NUMBERS_MAP = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}
LANGUAGES = ["de", "en", "es", "fr", "it", "pt", "nl", "sv"]
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SUMMARY_TYPES = ["brief", "narrative", "conversational", "no_speaker"]
WORDCAB_API_KEY = os.getenv("WORDCAB_API_KEY")
