# Copyright (c) 2023, The Wordcab team. All rights reserved.

import aiohttp
import asyncio
import re
from ast import literal_eval
from dotenv import load_dotenv
from functools import partial
from typing import Dict, List

from slack_bolt.async_app import AsyncApp

from wordcab import start_summary, retrieve_job, retrieve_summary
from wordcab.config import AVAILABLE_AUDIO_FORMATS, AVAILABLE_GENERIC_FORMATS
from wordcab.core_objects import GenericSource, AudioSource

from models import JobData
from config import (
    EMOJI_FLAGS_MAP,
    EMOJI_NUMBERS_MAP,
    LANGUAGES,
    SLACK_BOT_TOKEN,
    SLACK_SIGNING_SECRET,
    SUMMARY_TYPES,
    WORDCAB_API_KEY,
)


load_dotenv()


class WorcabSlackBot:
    def __init__(self):
        self.app = AsyncApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
        
        self.wordcab_api_key = WORDCAB_API_KEY
        
        self.app.event({"type": "message", "subtype": "file_share"})(self.file_share)
        self.app.event("message")(self.message)
        
        self.accepted_audio_formats = AVAILABLE_AUDIO_FORMATS
        self.accepted_generic_formats = AVAILABLE_GENERIC_FORMATS
        
        # Multi requests support
        self.jobs_queue = []
        self.jobs_queue_lock = asyncio.Lock()
        self.needs_processing = asyncio.Event()
        self.needs_processing_timer = None
        self.max_batch_size = 1
        self.max_wait_time = 1


    async def file_share(self, body, say, logger):
        """Summarize the file and post the summary"""

        text, urls, channel, msg_id = await self._extract_info(body)
        summary_length, summary_type, source_lang, delete_job = await self._get_summarization_params(text)
        
        
        job = JobData(
            summary_length=summary_length,
            source_lang=source_lang,
            summary_type=summary_type,
            delete_job=delete_job,
            urls=urls,
            msg_id=msg_id
        )
        await self._add_job_reactions(job.num_tasks, source_lang, channel, msg_id)

        
        result = await self._process_job(job)
        
        await self._final_reaction(result, channel, msg_id, say)


    async def message(self, body, say, logger):
        """Watch for messages"""
        if f"<@U04RVRJJN86>" in body["event"]["text"]:
            await say(
                """
                    Hi there! 🤗\n\nI'm your new Summarization assistant. Post any files in this channel and I'll summarize them for you.\n\nTo choose the summarization parameters, use the following syntax:\n\n`[summary_length] [summary_type] [source_lang] [delete_job]`\n\ne.g. `2 narrative True` or `1,3,5 no_speaker False` or `1 3 5 conversational fr`\n\n_Note that the order of the parameters doesn't matter._\n\n*Default Parameters if not specified:*\n- summary_length: `1,3,5`\n- summary_type: `narrative`\n- source_lang: `en`\n- delete_job: `True`
                """
            )


    async def _extract_info(self, body: Dict[str, str]):
        """Extract the information from the Slack event body"""
        text = body["event"]["text"]
        urls = [f["url_private_download"] for f in body["event"]["files"]]
        channel = body["event"]["channel"]
        msg_id = body["event"]["ts"]
        
        return text, urls, channel, msg_id


    async def _get_summarization_params(self, text: str):
        """Extract the summarization parameters from the Slack event text"""
        summary_length = list(set([int(s) for s in re.findall(r'\d+', text) if int(s) <= 5]))
        if not summary_length:
            summary_length = [1, 3, 5]
        
        summary_type = list(set([s for s in text.split() if s in SUMMARY_TYPES]))
        if not summary_type:
            summary_type = ["narrative"]

        source_lang = list(set([s for s in text.split() if s in LANGUAGES]))
        if not source_lang:
            source_lang = "en"
        elif len(source_lang) > 1:
            source_lang = source_lang[0]
        
        delete_job = re.findall(r'True|False|true|false', text)
        if not delete_job:
            delete_job = "True"
        elif len(delete_job) > 1:
            delete_job = delete_job[0]
        return summary_length, summary_type, source_lang, literal_eval(delete_job)
            

    async def _add_job_reactions(self, num_tasks: int, source_lang: str, channel: str, msg_id: str) -> None:

        """Add reactions to the message to indicate the number of jobs and the source language"""
        if num_tasks > 10:
            await self.app.client.reactions_add(
                channel=channel,
                name="ten",
                timestamp=msg_id,
            )
            await self.app.client.reactions_add(
                channel=channel,
                name="heavy_plus_sign",
                timestamp=msg_id,
            )

        else:
            await self.app.client.reactions_add(
                channel=channel,
                name=f"{EMOJI_NUMBERS_MAP[num_tasks]}",
                timestamp=msg_id,
            )

        await self.app.client.reactions_add(
            name=f"{EMOJI_FLAGS_MAP[source_lang]}",
            channel=channel,
            timestamp=msg_id,
        )
        
        return None


    async def _final_reaction(self, result: Dict[str, str], channel: str, msg_id: str, say: callable):
        """Add final reaction to the message about the job status"""
        if result["status"] == "success":
            await self.app.client.reactions_add(
                channel=channel,
                name="white_check_mark",
                timestamp=msg_id,
            )
        elif result["status"] == "error":
            await self.app.client.reactions_add(
                channel=channel,
                name="x",
                timestamp=msg_id,
            )
            await say(
                text=result["error"],
                thread_ts=msg_id,
            )


    def schedule_processing_if_needed(self):
        if len(self.jobs_queue) >= self.max_batch_size:
            self.needs_processing.set()
        elif self.jobs_queue:
            self.needs_processing_timer = asyncio.get_event_loop().call_at(
                self.jobs_queue[0]["time"] + self.max_wait_time, self.needs_processing.set
            )


    async def _process_job(self, job: JobData) -> None:
        """Add the job with tasks to the queue and wait for the job to be done"""
        try:
            new_job = {
                "done_event": asyncio.Event(),
                "time": asyncio.get_event_loop().time(),
                "data": job,
            }
            async with self.jobs_queue_lock:
                self.jobs_queue.append(new_job)
                self.schedule_processing_if_needed()
                
            await new_job["done_event"].wait()
            
            if new_job["status"] == "success":
                return {"status": "success"}
            elif new_job["status"] == "error":
                return {"status": "error", "error": new_job["error"]}

        except Exception as e:
            return {"status": "error", "error": str(e)}


    async def runner(self):
        """Process the jobs in the queue"""
        while True:
            await self.needs_processing.wait()
            self.needs_processing.clear()
            if self.needs_processing_timer is not None:
                self.needs_processing_timer.cancel()
                self.needs_processing_timer = None

            async with self.jobs_queue_lock:
                if self.jobs_queue:
                    longest_wait = asyncio.get_event_loop().time() - self.jobs_queue[0]["time"]
                else:
                    longest_wait = None
                job_batch = self.jobs_queue[:self.max_batch_size]
                del self.jobs_queue[:self.max_batch_size]
                self.schedule_processing_if_needed()

            for job in job_batch:
                try:
                    job_names = await self._launch_job_tasks(job["data"])
                    job["status"] = "success"
                    for job_name in job_names:
                        asyncio.create_task(self._monitor_job_status(job_name))
                except Exception as e:
                    job["status"] = "error"
                    job["error"] = str(e)
                finally:
                    job["done_event"].set()
            del job_batch


    async def _launch_job_tasks(self, job: JobData) -> None:
        """Process the job"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._summarization_task(url, summary_type, job.source_lang, job.summary_length)
                for summary_type in job.summary_type
                for url in job.urls
            ]
            
            job_names = await asyncio.gather(*tasks)
            
        return job_names


    async def _summarization_task(self, url: str, summary_type: str, source_lang: str, summary_lens: List[int]) -> str:
        """Launch a summarization job based on the input parameters and return the job name"""
        file_type = await self._check_file_extension(url.split("/")[-1])
        
        if file_type == "audio":
            source = AudioSource(url=url)
        elif file_type == "generic":
            source = GenericSource(url=url)
        else:
            accepted_formats = [f"`{format}`" for format in self.accepted_audio_formats + self.accepted_generic_formats]
            raise Exception(
                f"Invalid file extension: `{file_type}`\nAccepted formats: {' '.join(accepted_formats)}"
            )
            
        summarize_job = await asyncio.get_event_loop().run_in_executor(
            None, partial(
                start_summary,
                source_object=source,
                display_name="slack",
                source_lang=source_lang,
                summary_type=summary_type,
                summary_lens=summary_lens,
                tags=["slack", "slackbot"],
                api_key=self.wordcab_api_key,
            )
        )

        return summarize_job.job_name


    async def _monitor_job_status(self, job_name: str) -> None:
        """Monitor the job status and return the summary_id when the job is done"""
        while True:
            job = await asyncio.get_event_loop().run_in_executor(
                None, partial(retrieve_job, job_name=job_name, api_key=self.wordcab_api_key)
            )
            if job.status == "done":
                break
            else:
                await asyncio.sleep(5)

        asyncio.create_task(self._get_summary(job.summary_id))
        
        return None

    
    async def _get_summary(self, summary_id: str) -> str:
        """Get the summary from the summary_id"""
        summary = await asyncio.get_event_loop().run_in_executor(
            None, partial(retrieve_summary, summary_id=summary_id, api_key=self.wordcab_api_key)
        )
        
        return summary.summary


    async def _check_file_extension(self, filename: str) -> str:
        """Check the file extension and return the file type"""
        file_extension = f".{filename.split('.')[-1]}"

        if file_extension in self.accepted_audio_formats:
            return "audio"
        elif file_extension in self.accepted_generic_formats:
            return "generic"

        return file_extension


    async def _download_file_from_slack(
        self, session: aiohttp.ClientSession, url: str, headers: Dict[str, str] = {}
    ) -> bytes:
        async with session.get(url, headers=headers) as response:
            file_content = await response.read()

        return file_content
