# Copyright (c) 2023, The Wordcab team. All rights reserved.

import logging

from fastapi import FastAPI, Request

from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from slack_bot import app


api = FastAPI()
app_handler = AsyncSlackRequestHandler(app)


@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    import uvicorn
    uvicorn.run("main:api", host="0.0.0.0", port=8000, log_level="info", reload=True)
