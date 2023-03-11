# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Utility functions for the wordcab_slack package."""

import asyncio
import io
import re
from ast import literal_eval
from functools import partial
from typing import Dict, List, Tuple

from wordcab import delete_job, retrieve_job, retrieve_summary, start_summary
from wordcab.core_objects import AudioSource, BaseSummary, GenericSource

from wordcab_slack.models import JobData


async def _check_file_extension(
    filename: str,
    accepted_audio_formats: List[str],
    accepted_generic_formats: List[str],
) -> str:
    """
    Check the file extension and return the file type.

    Args:
        filename (str): The filename to check
        accepted_audio_formats (List[str]): The list of accepted audio formats
        accepted_generic_formats (List[str]): The list of accepted generic formats

    Returns:
        str: The file type
    """
    file_extension = f".{filename.split('.')[-1]}"

    if file_extension in accepted_audio_formats:
        return "audio"
    elif file_extension in accepted_generic_formats:
        return "generic"

    return file_extension


async def delete_finished_jobs(job_names: List[str], api_key: str) -> None:
    """
    Delete the job from wordcab.

    Args:
        job_names (List[str]): The list of job names to delete
        api_key (str): The Wordcab api key
    """
    for job_name in job_names:
        await asyncio.get_event_loop().run_in_executor(
            None,
            partial(delete_job, job_name=job_name, warning=False, api_key=api_key),
        )


async def extract_info(body: Dict[str, str]) -> Tuple[str, List[str], str, str]:
    """
    Extract the information from the Slack event body.

    Args:
        body (Dict[str, str]): The Slack event body

    Returns:
        Tuple[str, List[str], str, str]: The text, file_ids, channel and message id
    """
    text = body["event"]["text"]
    file_ids = [file["id"] for file in body["event"]["files"]]
    channel = body["event"]["channel"]
    msg_id = body["event"]["ts"]

    return text, file_ids, channel, msg_id


async def format_files_to_upload(summary: BaseSummary) -> List[Dict[str, io.StringIO]]:
    """
    Format the summary to upload to Slack as a List of Dicts with the file name and the content.

    Args:
        summary (BaseSummary): The BaseSummary object from wordcab-python

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
                    " ".join([summary.summary for summary in val["structured_summary"]])
                ),
                "title": f"{summary_type}_{key}_{summary_id}",
                "alt_text": f"Summary {summary_id} of type {summary_type} with a length of {key}.",
                "snippet_type": "text",
            }
        )

    return file_uploads


async def _get_file_names(urls: List[str]) -> List[str]:
    """
    Get the file names from the urls.

    Args:
        urls (List[str]): The list of urls to get the file names from

    Returns:
        List[str]: The list of file names
    """
    return [url.split("/")[-1] for url in urls]


async def get_summarization_params(
    text: str, available_summary_types: List[str], available_languages: List[str]
) -> Tuple[List[int], List[str], str, bool]:
    """
    Extract the summarization parameters from the Slack event text.

    Args:
        text (str): The Slack event text
        available_summary_types (List[str]): The list of available summary types
        available_languages (List[str]): The list of available languages

    Returns:
        Tuple[List[int], List[str], str, bool]: The summary length, summary type, source language and delete job
    """
    text = re.sub(r"<@\w+>", "", text)  # Remove the @user from the text

    summary_length = list({int(s) for s in re.findall(r"\d+", text) if int(s) <= 5})
    if not summary_length:
        summary_length = [1, 3, 5]

    summary_type = list({s for s in text.split() if s in available_summary_types})
    if not summary_type:
        summary_type = ["narrative"]

    source_lang = list({s for s in text.split() if s in available_languages})
    if not source_lang:
        source_lang = "en"
    elif isinstance(source_lang, list):
        source_lang = source_lang[0]

    delete_job = re.findall(r"True|False|true|false|TRUE|FALSE", text)
    if not delete_job:
        delete_job = "True"
    elif isinstance(delete_job, list):
        delete_job = delete_job[0]

    return summary_length, summary_type, source_lang, literal_eval(delete_job)


async def get_summary(summary_id: str, api_key: str) -> BaseSummary:
    """
    Get the summary from the summary_id.

    Args:
        summary_id (str): The summary_id to get the summary from
        api_key (str): The Wordcab api key

    Returns:
        BaseSummary: The summary object from wordcab-python
    """
    summary = await asyncio.get_event_loop().run_in_executor(
        None,
        partial(retrieve_summary, summary_id=summary_id, api_key=api_key),
    )

    return summary


async def _launch_job_tasks(
    job: JobData,
    accepted_audio_formats: List[str],
    accepted_generic_formats: List[str],
    bot_token: str,
    api_key: str,
) -> List[str]:
    """
    Process the job and launch the tasks.

    Args:
        job (JobData): The job data to process including the tasks
        accepted_audio_formats (List[str]): The list of accepted audio formats
        accepted_generic_formats (List[str]): The list of accepted generic formats
        bot_token (str): The Slack bot token
        api_key (str): The Wordcab api key

    Returns:
        List[str]: The list of job names
    """
    tasks = [
        _summarization_task(
            url=url,
            summary_type=summary_type,
            source_lang=job.source_lang,
            summary_lens=job.summary_length,
            accepted_audio_formats=accepted_audio_formats,
            accepted_generic_formats=accepted_generic_formats,
            bot_token=bot_token,
            api_key=api_key,
        )
        for summary_type in job.summary_type
        for url in job.urls
    ]
    job_names = await asyncio.gather(*tasks)

    return job_names


async def monitor_job_status(job_name: str, api_key: str) -> str:
    """
    Monitor the job status and return the summary_id when the job is done.

    Args:
        job_name (str): The job name to monitor
        api_key (str): The Wordcab api key

    Returns:
        str: The summary_id of the job
    """
    while True:
        job = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(retrieve_job, job_name=job_name, api_key=api_key),
        )
        if job.job_status == "SummaryComplete":
            break
        elif job.job_status == "Error" or job.job_status == "Deleted":
            break
        else:
            await asyncio.sleep(5)

    return job.summary_details["summary_id"]


async def _summarization_task(
    url: str,
    summary_type: str,
    source_lang: str,
    summary_lens: List[int],
    accepted_audio_formats: List[str],
    accepted_generic_formats: List[str],
    bot_token: str,
    api_key: str,
) -> str:
    """
    Launch a summarization job based on the input parameters and return the job name.

    Args:
        url (str): The url of the file to summarize
        summary_type (str): The type of summary to generate
        source_lang (str): The language of the source file
        summary_lens (List[int]): The list of summary lengths to generate
        accepted_audio_formats (List[str]): The list of accepted audio formats
        accepted_generic_formats (List[str]): The list of accepted generic formats
        bot_token (str): The Slack bot token
        api_key (str): The Wordcab api key

    Raises:
        Exception: If the file extension is not supported

    Returns:
        str: The job name of the summarization job launched
    """
    file_type = await _check_file_extension(
        filename=url.split("/")[-1],
        accepted_audio_formats=accepted_audio_formats,
        accepted_generic_formats=accepted_generic_formats,
    )
    url_headers = {"Authorization": f"Bearer {bot_token}"}

    if file_type == "audio":
        source = AudioSource(url=url, url_headers=url_headers)
    elif file_type == "generic":
        source = GenericSource(url=url, url_headers=url_headers)
    else:
        accepted_formats = [
            f"`{accepted_format}`"
            for accepted_format in accepted_audio_formats + accepted_generic_formats
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
            api_key=api_key,
        ),
    )

    return summarize_job.job_name
