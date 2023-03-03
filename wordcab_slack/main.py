# Copyright (c) 2023, The Wordcab team. All rights reserved.

import asyncio
import logging

from fastapi import FastAPI, Request

from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from slack_bot import WorcabSlackBot


api = FastAPI()
bot = WorcabSlackBot()
app_handler = AsyncSlackRequestHandler(bot.app)


@api.on_event("startup")
async def startup():
    logging.info("Starting up...")
    asyncio.create_task(bot.runner())


@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    import uvicorn
    uvicorn.run("main:api", host="0.0.0.0", port=8000, log_level="info", reload=True)