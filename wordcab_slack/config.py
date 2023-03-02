# Copyright (c) 2023, The Wordcab team. All rights reserved.

import os
from dotenv import load_dotenv


load_dotenv()


SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
SUMMARY_TYPES = ["narrative", "conversational", "no_speaker", "reason_conclusion"]
TARGET_LANGUAGES = ["en", "fr", "de", "es", "it", "nl", "sv"]
