# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Slack bot for Wordcab summarization service."""

import asyncio
import io
import re
from ast import literal_eval
from functools import partial
from loguru import logger as log
from typing import Dict, List, Tuple, Union

from slack_bolt.async_app import AsyncApp
from wordcab import retrieve_job, retrieve_summary, start_summary
from wordcab.config import AVAILABLE_AUDIO_FORMATS, AVAILABLE_GENERIC_FORMATS
from wordcab.core_objects import (
    AudioSource,
    BaseSummary,
    GenericSource,
    StructuredSummary,
)

from wordcab_slack.config import (
    EMOJI_FLAGS_MAP,
    EMOJI_NUMBERS_MAP,
    LANGUAGES,
    SLACK_BOT_TOKEN,
    SLACK_SIGNING_SECRET,
    SUMMARY_TYPES,
    WORDCAB_API_KEY,
)
from wordcab_slack.models import JobData


class WorcabSlackBot:
    def __init__(self) -> None:
        """Slack bot for Wordcab summarization service."""
        self.slack_bot_token = SLACK_BOT_TOKEN
        self.wordcab_api_key = WORDCAB_API_KEY
        self.app = AsyncApp(
            token=self.slack_bot_token, signing_secret=SLACK_SIGNING_SECRET
        )

        with open("bot-description.txt") as f:
            self.bot_description = f.read()

        self.app.event({"type": "message", "subtype": "file_share"})(self.file_share)
        self.app.event({"type": "message", "subtype": "message_changed"})(
            self.message_changed
        )
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

    async def file_share(self, body, say, logger) -> None:
        """
        Summarize the file and post the summary.

        Args:
            body (Dict[str, str]): The Slack event body
            say (Callable): The say function to post the summary
            logger (Callable): The logger function to log errors
        """
        # Wrap the function in a try/except block to catch any errors
        try:
            text, urls, channel, msg_id = await self._extract_info(body)
            (
                summary_length,
                summary_type,
                source_lang,
                delete_job,
            ) = await self._get_summarization_params(text)

            job = JobData(
                summary_length=summary_length,
                source_lang=source_lang,
                summary_type=summary_type,
                delete_job=delete_job,
                urls=urls,
                msg_id=msg_id,
            )
            await self._add_job_reactions(job.num_tasks, source_lang, channel, msg_id)

            result = await self._process_job(job, channel, msg_id)
            status = result["status"]

            if status == "error":
                raise Exception(result["error"])

            job_names = result["job_names"]

            await self._loading_reaction(channel, msg_id)

            tasks = [self._monitor_job_status(job_name) for job_name in job_names]
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                summary = await self._get_summary(result)
                await self._post_summary(summary, channel, msg_id)

            await self._final_checking_reaction(channel, msg_id)

        except Exception as e:
            await self._error_reaction(channel, msg_id, say, str(e))

    async def message_changed(self, body, say, logger):
        """Delete the responses to the deleted message if any exist from the bot."""
        if "subtype" in body["event"]["message"]:
            if body["event"]["message"]["subtype"] == "tombstone":
                try:
                    replies = await self.app.client.conversations_replies(
                        channel=body["event"]["channel"],
                        ts=body["event"]["previous_message"]["ts"],
                        limit=1000,
                        inclusive=True,
                    )
                    for reply in replies["messages"]:
                        if reply["user"] == "U04RVRJJN86":
                            await self.app.client.chat_delete(
                                channel=body["event"]["channel"],
                                ts=reply["ts"],
                            )
                except Exception as e:
                    pass  # Allow to ignore message deletion not related to the thread replies from the bot

    async def message(self, body, say, logger):
        """
        Watch for messages.

        Args:
            body (Dict[str, str]): The Slack event body
            say (Callable): The say function to post the summary
            logger (Callable): The logger function to log errors
        """
        if "text" in body["event"]:
            if f"<@U04RVRJJN86>" in body["event"]["text"]:
                await say(self.bot_description)
        else:
            pass

    async def _extract_info(
        self, body: Dict[str, str]
    ) -> Tuple[str, List[str], str, str]:
        """
        Extract the information from the Slack event body.

        Args:
            body (Dict[str, str]): The Slack event body

        Returns:
            Tuple[str, List[str], str, str]: The text, urls, channel and message id
        """
        text = body["event"]["text"]
        urls = [f["url_private_download"] for f in body["event"]["files"]]
        channel = body["event"]["channel"]
        msg_id = body["event"]["ts"]

        return text, urls, channel, msg_id

    async def _get_summarization_params(
        self, text: str
    ) -> Tuple[List[int], List[str], str, bool]:
        """
        Extract the summarization parameters from the Slack event text.

        Args:
            text (str): The Slack event text

        Returns:
            Tuple[List[int], List[str], str, bool]: The summary length, summary type, source language and delete job
        """
        summary_length = list({int(s) for s in re.findall(r"\d+", text) if int(s) <= 5})
        if not summary_length:
            summary_length = [1, 3, 5]

        summary_type = list({s for s in text.split() if s in SUMMARY_TYPES})
        if not summary_type:
            summary_type = ["narrative"]

        source_lang = list({s for s in text.split() if s in LANGUAGES})
        if not source_lang:
            source_lang = "en"
        if len(source_lang) > 1:
            source_lang = source_lang[0]

        delete_job = re.findall(r"True|False|true|false", text)
        if not delete_job:
            delete_job = "True"
        elif len(delete_job) > 1:
            delete_job = delete_job[0]

        return summary_length, summary_type, source_lang, literal_eval(delete_job)

    async def _add_job_reactions(
        self, num_tasks: int, source_lang: str, channel: str, msg_id: str
    ) -> None:
        """
        Add reactions to the message to indicate the number of jobs and the source language.

        Args:
            num_tasks (int): The number of tasks to be executed
            source_lang (str): The source language
            channel (str): The channel id
            msg_id (str): The message id
        """
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

    async def _loading_reaction(self, channel: str, msg_id: str) -> None:
        """
        Add a loading reaction to the message to indicate that the job is in progress.

        Args:
            channel (str): The channel id
            msg_id (str): The message id
        """
        await self.app.client.reactions_add(
            channel=channel,
            name="hourglass_flowing_sand",
            timestamp=msg_id,
        )

    async def _final_checking_reaction(self, channel: str, msg_id: str) -> None:
        """
        Add final reaction to the message to indicate that the job is done.

        Args:
            channel (str): The channel id
            msg_id (str): The message id
        """
        await self.app.client.reactions_remove(
            channel=channel,
            name="hourglass_flowing_sand",
            timestamp=msg_id,
        )
        await self.app.client.reactions_add(
            channel=channel,
            name="white_check_mark",
            timestamp=msg_id,
        )

    async def _error_reaction(
        self, channel: str, msg_id: str, say: callable, error: str
    ) -> None:
        """
        Add an error reaction to the message to indicate that the job failed.

        Args:
            channel (str): The channel id
            msg_id (str): The message id
            say (callable): The say function
            error (str): The error message
        """
        reactions_obj = await self.app.client.reactions_get(
            channel=channel, timestamp=msg_id
        )
        if "reactions" in reactions_obj["message"]:
            reactions = [
                reaction["name"] for reaction in reactions_obj["message"]["reactions"]
            ]

            if "hourglass_flowing_sand" in reactions:
                await self.app.client.reactions_remove(
                    channel=channel,
                    name="hourglass_flowing_sand",
                    timestamp=msg_id,
                )

        await self.app.client.reactions_add(
            channel=channel,
            name="x",
            timestamp=msg_id,
        )
        await say(
            text=error,
            thread_ts=msg_id,
        )

    async def _post_summary(
        self,
        summary: Dict[str, Dict[str, List[StructuredSummary]]],
        channel: str,
        msg_id: str,
    ) -> None:
        """
        Post the retrieved summaries to the thread as txt files.

        Args:
            summary (Dict[str, Dict[str, List[StructuredSummary]]]): The BaseSummary object from wordcab-python
            channel (str): The channel id
            msg_id (str): The message id
        """
        file_uploads = await self._format_files_to_upload(summary)

        await self.app.client.files_upload_v2(
            title=f"{summary.job_name} - {summary.summary_type}",
            file_uploads=file_uploads,
            channel=channel,
            thread_ts=msg_id,
        )

    async def _format_files_to_upload(
        self, summary: Dict[str, Dict[str, List[StructuredSummary]]]
    ) -> List[Dict[str, io.StringIO]]:
        """
        Format the summary to upload to Slack as a List of Dicts with the file name and the content.

        Args:
            summary (Dict[str, Dict[str, List[StructuredSummary]]]): The BaseSummary object from wordcab-python

        Returns:
            List[Dict[str, io.StringIO]]: The list of files to upload with their metadata
        """
        summary_type = summary.summary_type
        summary_id = summary.summary_id

        file_uploads: List[Dict[str, io.StringIO]] = []
        for key, val in summary.summary.items():
            file_uploads.append(
                {
                    "filename": f"{summary_type}_{key}_{summary_id}.txt",
                    "file": io.StringIO(
                        " ".join(
                            [summary.summary for summary in val["structured_summary"]]
                        )
                    ),
                    "title": f"{summary_type}_{key}_{summary_id}",
                    "alt_text": f"Summary {summary_id} of type {summary_type} with a length of {key}.",
                    "snippet_type": "text",
                }
            )

        return file_uploads

    def schedule_processing_if_needed(self):
        """Schedule the processing of the jobs queue if needed."""
        if len(self.jobs_queue) >= self.max_batch_size:
            self.needs_processing.set()
        elif self.jobs_queue:
            self.needs_processing_timer = asyncio.get_event_loop().call_at(
                self.jobs_queue[0]["time"] + self.max_wait_time,
                self.needs_processing.set,
            )

    async def _process_job(
        self, job: JobData, channel: str, msg_id: str
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Add the job with tasks to the queue and wait for the job to be done.

        Args:
            job (JobData): The job data to process including the tasks
            channel (str): The channel id
            msg_id (str): The message id

        Returns:
            Dict[str, Union[str, List[str]]]: The status of the job and the job names if successful, or
            the error message if not.
        """
        try:
            new_job = {
                "done_event": asyncio.Event(),
                "time": asyncio.get_event_loop().time(),
                "data": job,
                "channel": channel,
                "msg_id": msg_id,
                "status": "pending",
            }
            async with self.jobs_queue_lock:
                self.jobs_queue.append(new_job)
                self.schedule_processing_if_needed()

            await new_job["done_event"].wait()

            if new_job["status"] == "success":
                return {"status": "success", "job_names": new_job["job_names"]}
            elif new_job["status"] == "error":
                return {"status": "error", "error": new_job["error"]}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def runner(self):
        """Process the jobs in the queue. This is a coroutine that should be run at startup."""
        while True:
            await self.needs_processing.wait()
            self.needs_processing.clear()
            if self.needs_processing_timer is not None:
                self.needs_processing_timer.cancel()
                self.needs_processing_timer = None

            async with self.jobs_queue_lock:
                if self.jobs_queue:
                    longest_wait = (
                        asyncio.get_event_loop().time() - self.jobs_queue[0]["time"]
                    )
                else:
                    longest_wait = None
                log.debug(f"Longest wait: {longest_wait}")
                job_batch = self.jobs_queue[: self.max_batch_size]
                del self.jobs_queue[: self.max_batch_size]
                self.schedule_processing_if_needed()

            for job in job_batch:
                try:
                    job_names = await self._launch_job_tasks(job["data"])
                    job["status"] = "success"
                    job["job_names"] = job_names
                except Exception as e:
                    job["status"] = "error"
                    job["error"] = str(e)
                finally:
                    job["done_event"].set()
            del job_batch

    async def _launch_job_tasks(self, job: JobData) -> List[str]:
        """
        Process the job and launch the tasks.

        Args:
            job (JobData): The job data to process including the tasks

        Returns:
            List[str]: The list of job names
        """
        tasks = [
            self._summarization_task(
                url, summary_type, job.source_lang, job.summary_length
            )
            for summary_type in job.summary_type
            for url in job.urls
        ]
        job_names = await asyncio.gather(*tasks)

        return job_names

    async def _summarization_task(
        self, url: str, summary_type: str, source_lang: str, summary_lens: List[int]
    ) -> str:
        """
        Launch a summarization job based on the input parameters and return the job name.

        Args:
            url (str): The url of the file to summarize
            summary_type (str): The type of summary to generate
            source_lang (str): The language of the source file
            summary_lens (List[int]): The list of summary lengths to generate

        Returns:
            str: The job name of the summarization job launched
        """
        file_type = await self._check_file_extension(url.split("/")[-1])
        url_headers = {"Authorization": f"Bearer {self.slack_bot_token}"}

        if file_type == "audio":
            source = AudioSource(url=url, url_headers=url_headers)
        elif file_type == "generic":
            source = GenericSource(url=url, url_headers=url_headers)
        else:
            accepted_formats = [
                f"`{format}`"
                for format in self.accepted_audio_formats
                + self.accepted_generic_formats
            ]
            raise Exception(
                f"Invalid file extension: `{file_type}`\nAccepted formats: {' '.join(accepted_formats)}"
            )

        summarize_job = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                start_summary,
                source_object=source,
                display_name="slack",
                source_lang=source_lang,
                summary_type=summary_type,
                summary_lens=summary_lens,
                tags=["slack", "slackbot"],
                api_key=self.wordcab_api_key,
            ),
        )

        return summarize_job.job_name

    async def _monitor_job_status(self, job_name: str) -> str:
        """
        Monitor the job status and return the summary_id when the job is done.

        Args:
            job_name (str): The job name to monitor

        Returns:
            str: The summary_id of the job
        """
        while True:
            job = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(retrieve_job, job_name=job_name, api_key=self.wordcab_api_key),
            )
            if job.job_status == "SummaryComplete":
                break
            elif job.job_status == "Error" or job.job_status == "Deleted":
                break
            else:
                await asyncio.sleep(5)

        return job.summary_details["summary_id"]

    async def _get_summary(self, summary_id: str) -> BaseSummary:
        """
        Get the summary from the summary_id.

        Args:
            summary_id (str): The summary_id to get the summary from

        Returns:
            BaseSummary: The summary object from wordcab-python
        """
        summary = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                retrieve_summary, summary_id=summary_id, api_key=self.wordcab_api_key
            ),
        )

        return summary

    async def _check_file_extension(self, filename: str) -> str:
        """
        Check the file extension and return the file type.

        Args:
            filename (str): The filename to check

        Returns:
            str: The file type
        """
        file_extension = f".{filename.split('.')[-1]}"

        if file_extension in self.accepted_audio_formats:
            return "audio"
        elif file_extension in self.accepted_generic_formats:
            return "generic"

        return file_extension
