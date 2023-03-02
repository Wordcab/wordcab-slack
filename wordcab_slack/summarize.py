# Copyright (c) 2023, The Wordcab team. All rights reserved.

import aiohttp


class Summarizer:
    def __init__(self) -> None:
        pass
    
    async def download_file_from_slack(url, headers):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                file_content = await response.read()
                return file_content