# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Slack bot for Wordcab summarization service."""

import asyncio
from typing import Dict, List, Union

from loguru import logger as log
from slack_bolt.async_app import AsyncApp
from wordcab.config import AVAILABLE_AUDIO_FORMATS, AVAILABLE_GENERIC_FORMATS
from wordcab.core_objects import BaseSummary

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
from wordcab_slack.utils import (
    _get_file_names,
    _launch_job_tasks,
    delete_finished_jobs,
    extract_info,
    extract_transcript_ids,
    format_files_to_upload,
    get_summarization_params,
    get_summary,
    monitor_job_status,
)


class WorcabSlackBot:
    """Slack bot for Wordcab summarization service."""

    def __init__(self) -> None:
        """Initialize the bot."""
        self.slack_bot_token = SLACK_BOT_TOKEN
        self.wordcab_api_key = WORDCAB_API_KEY
        self.app = AsyncApp(
            token=self.slack_bot_token, signing_secret=SLACK_SIGNING_SECRET
        )

        with open("./bot-description.txt") as f:
            self.bot_description = f.read()

        self.app.event({"type": "message", "subtype": "file_share"})(self.file_share)
        self.app.event({"type": "message", "subtype": "message_changed"})(
            self.message_changed
        )
        self.app.event("message")(self.message)

        self.accepted_audio_formats = AVAILABLE_AUDIO_FORMATS
        self.accepted_generic_formats = AVAILABLE_GENERIC_FORMATS
        self.available_summary_types = SUMMARY_TYPES
        self.available_languages = LANGUAGES

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
        if "#botignore" in body["event"]["text"]:
            pass

        # Wrap the function in a try/except block to catch any errors
        try:
            text, file_ids, channel, msg_id = await extract_info(body=body)
            params = await get_summarization_params(
                text=text,
                available_summary_types=self.available_summary_types,
            )
            urls = await self._get_urls_from_file_ids(file_ids=file_ids)

            job = JobData(
                summary_length=params[0],
                summary_type=params[1],
                source_lang=params[2],
                target_lang=params[3],
                context_features=params[4],
                urls=urls,
                transcript_ids=None,
                msg_id=msg_id,
            )
            await self._add_job_reactions(
                job.num_tasks, job.source_lang, job.target_lang, channel, msg_id
            )

            result = await self._process_job(job, channel, msg_id)
            status = result["status"]

            if status == "error":
                raise Exception(result["error"])

            job_names = result["job_names"]
            file_names = result["file_names"]

            await self._loading_reaction(channel, msg_id)

            tasks = [
                monitor_job_status(job_name=job_name, api_key=self.wordcab_api_key)
                for job_name in job_names
            ]
            for completed_task, file_name in zip(
                asyncio.as_completed(tasks),
                file_names,
                strict=True,
            ):
                result = await completed_task
                summary = await get_summary(
                    summary_id=result, api_key=self.wordcab_api_key
                )
                await self._post_summary(summary, file_name, channel, msg_id)

            await self._final_checking_reaction(channel, msg_id)

            await delete_finished_jobs(
                job_names=job_names, api_key=self.wordcab_api_key
            )

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
                except Exception:  # noqa: S110
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
            if "<@U04RVRJJN86>" in body["event"]["text"]:
                await self.app.client.chat_postMessage(
                    channel=body["event"]["channel"],
                    thread_ts=body["event"]["ts"],
                    text=self.bot_description,
                )
            elif "transcript_id:" in body["event"]["text"]:
                try:
                    text, _, channel, msg_id = await extract_info(body=body)
                    text, transcript_ids = await extract_transcript_ids(text)
                    params = await get_summarization_params(
                        text=text,
                        available_summary_types=self.available_summary_types,
                    )

                    job = JobData(
                        summary_length=params[0],
                        summary_type=params[1],
                        source_lang=params[2],
                        target_lang=params[3],
                        context_features=params[4],
                        urls=None,
                        transcript_ids=transcript_ids,
                        msg_id=msg_id,
                    )
                    await self._add_job_reactions(
                        job.num_tasks, job.source_lang, job.target_lang, channel, msg_id
                    )

                    result = await self._process_job(job, channel, msg_id)
                    status = result["status"]

                    if status == "error":
                        raise Exception(result["error"])

                    job_names = result["job_names"]
                    file_names = result["file_names"]

                    await self._loading_reaction(channel, msg_id)

                    tasks = [
                        monitor_job_status(
                            job_name=job_name, api_key=self.wordcab_api_key
                        )
                        for job_name in job_names
                    ]
                    for completed_task, file_name in zip(
                        asyncio.as_completed(tasks),
                        file_names,
                        strict=True,
                    ):
                        result = await completed_task
                        summary = await get_summary(
                            summary_id=result, api_key=self.wordcab_api_key
                        )
                        await self._post_summary(summary, file_name, channel, msg_id)

                    await self._final_checking_reaction(channel, msg_id)

                except Exception as e:
                    await self._error_reaction(channel, msg_id, say, str(e))
        else:
            pass

    async def _add_job_reactions(
        self,
        num_tasks: int,
        source_lang: str,
        target_lang: str,
        channel: str,
        msg_id: str,
    ) -> None:
        """
        Add reactions to the message to indicate the number of jobs and the source language.

        Args:
            num_tasks (int): The number of tasks to be executed
            source_lang (str): The source language
            target_lang (str): The target language
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
        if target_lang != source_lang:
            await self.app.client.reactions_add(
                name=f"{EMOJI_FLAGS_MAP[target_lang]}",
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
        summary: BaseSummary,
        file_name: str,
        channel: str,
        msg_id: str,
    ) -> None:
        """
        Post the retrieved summaries to the thread as txt files.

        Args:
            summary (BaseSummary): The BaseSummary object from wordcab-python
            file_name (str): The name of the summarized input file
            channel (str): The channel id
            msg_id (str): The message id
        """
        file_uploads = await format_files_to_upload(summary=summary)

        await self.app.client.files_upload_v2(
            title=f"{summary.job_name} - {summary.summary_type}",
            file_uploads=file_uploads,
            filetype="text",
            channel=channel,
            initial_comment=f"Output(s) for `{file_name}`",
            thread_ts=msg_id,
            file_visibility="public",
        )

    async def _get_urls_from_file_ids(self, file_ids: List[str]) -> List[str]:
        """
        Get the URLs of the files from the file ids.

        Args:
            file_ids (List[str]): The file ids

        Returns:
            List[str]: The URLs of the files
        """
        urls = []
        for file_id in file_ids:
            file_info = await self.app.client.files_info(file=file_id)
            urls.append(file_info["file"]["url_private_download"])

        return urls

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
            Dict[str, Union[str, List[str]]]: The status of the job, the job names and the file names if successful,
            or the error message if not.
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
                self._schedule_processing_if_needed()

            await new_job["done_event"].wait()

            if new_job["status"] == "success":
                return {
                    "status": "success",
                    "job_names": new_job["job_names"],
                    "file_names": new_job["file_names"],
                }
            elif new_job["status"] == "error":
                return {"status": "error", "error": new_job["error"]}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _schedule_processing_if_needed(self):
        """Schedule the processing of the jobs queue if needed."""
        if len(self.jobs_queue) >= self.max_batch_size:
            self.needs_processing.set()
        elif self.jobs_queue:
            self.needs_processing_timer = asyncio.get_event_loop().call_at(
                self.jobs_queue[0]["time"] + self.max_wait_time,
                self.needs_processing.set,
            )

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
                log.info(f"Longest wait: {longest_wait}")
                job_batch = self.jobs_queue[: self.max_batch_size]
                del self.jobs_queue[: self.max_batch_size]
                self._schedule_processing_if_needed()

            for job in job_batch:
                try:
                    job_names = await _launch_job_tasks(
                        job=job["data"],
                        accepted_audio_formats=self.accepted_audio_formats,
                        accepted_generic_formats=self.accepted_generic_formats,
                        bot_token=self.slack_bot_token,
                        api_key=self.wordcab_api_key,
                    )
                    file_names = await _get_file_names(data=job["data"])
                    job["status"] = "success"
                    job["job_names"] = job_names
                    job["file_names"] = file_names
                except Exception as e:
                    job["status"] = "error"
                    job["error"] = str(e)
                finally:
                    job["done_event"].set()
            del job_batch
