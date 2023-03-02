# Copyright (c) 2023, The Wordcab team. All rights reserved.

import re
from dotenv import load_dotenv

from slack_bolt.async_app import AsyncApp

from models import SummaryData
from config import (
    EMOJI_FLAGS_MAP,
    EMOJI_NUMBERS_MAP,
    SLACK_BOT_TOKEN,
    SLACK_SIGNING_SECRET,
    SUMMARY_TYPES,
    TARGET_LANGUAGES,
)


load_dotenv()


app = AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)


@app.event({"type": "message", "subtype": "file_share"})
async def file_share(body, say, logger):
    """Summarize the file and post the summary"""
    text = body["event"]["text"]
    urls = [f["url_private_download"] for f in body["event"]["files"]]
    msg_id = body["event"]["ts"]
    
    summary_length = list(set([int(s) for s in re.findall(r'\d+', text) if int(s) <= 5]))
    if not summary_length:
        summary_length = [1, 3, 5]
    
    summary_type = list(set([s for s in text.split() if s in SUMMARY_TYPES]))
    if not summary_type:
        summary_type = ["narrative"]
        
    target_lang = list(set([s for s in text.split() if s in TARGET_LANGUAGES]))
    if not target_lang:
        target_lang = "en"
    elif len(target_lang) > 1:
        target_lang = target_lang[0]
    
    delete_job = re.findall(r'True|False|true|false', text)
    if not delete_job:
        delete_job = "True"
    elif len(delete_job) > 1:
        delete_job = delete_job[0]
    
    data = SummaryData(
        summary_type=summary_type,
        summary_length=summary_length,
        target_lang=target_lang,
        delete_job=delete_job,
        urls=urls,
        msg_id=msg_id
    )
    
    # TODO: Send data to the summarization service

    await app.client.reactions_add(
        channel=body["event"]["channel"],
        name=f"{EMOJI_NUMBERS_MAP[data.num_tasks]}",
        timestamp=body["event"]["ts"]
    )
    await app.client.reactions_add(
        channel=body["event"]["channel"],
        name=f"{EMOJI_FLAGS_MAP[data.target_lang]}",
        timestamp=body["event"]["ts"]
    )


@app.event("message")
async def message(body, say, logger):
    """Watch for messages"""
    if f"<@U04RVRJJN86>" in body["event"]["text"]:
        await say(
            """
                Hi there! 🤗\n\nI'm your new Summarization assistant. Post any files in this channel and I'll summarize them for you.\n\nTo choose the summarization parameters, use the following syntax:\n\n`[summary_length] [summary_type] [target_lang] [delete_job]`\n\ne.g. `2 narrative True` or `1,3,5 no_speaker False` or `1 3 5 conversational fr`\n\n_Note that the order of the parameters doesn't matter._\n\n*Default Parameters if not specified:*\n- summary_length: `1,3,5`\n- summary_type: `narrative`\n- target_language: `en`\n- delete_job: `True`
            """
        )
