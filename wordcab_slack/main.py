# Copyright (c) 2023, The Wordcab team. All rights reserved.

import asyncio
import logging

from fastapi import FastAPI, Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from wordcab_slack.slack_bot import WorcabSlackBot


api = FastAPI(title="Wordcab Slack Bot", version="1.0.0")
bot = WorcabSlackBot()
app_handler = AsyncSlackRequestHandler(bot.app)


@api.on_event("startup")
async def startup():
    logging.info("Starting up...")
    asyncio.create_task(bot.runner())


@api.post("/slack/events", tags=["slack"])
async def endpoint(req: Request):
    return await app_handler.handle(req)


@api.get("/health", tags=["status"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    import uvicorn

    uvicorn.run(
        "wordcab_slack.main:api",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
    )
