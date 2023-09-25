# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Utility functions for the wordcab_slack package."""

import asyncio
import io
import re
from functools import partial
from typing import Dict, List, Tuple, Union

from wordcab import delete_job, retrieve_job, retrieve_summary, start_summary
from wordcab.core_objects import (
    AudioSource,
    BaseSummary,
    GenericSource,
    WordcabTranscriptSource,
)

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


async def delete_finished_jobs(
    job_names: List[str], api_key: str
) -> None:  # pragma: no cover
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
    file_ids = (
        [file["id"] for file in body["event"]["files"]]
        if "files" in body["event"]
        else None
    )
    channel = body["event"]["channel"]
    msg_id = body["event"]["ts"]

    return text, file_ids, channel, msg_id


async def extract_transcript_ids(text: str) -> Tuple[str, str]:
    """
    Extract the transcript ids from the Slack event text and return it with the text without the transcript id.

    Args:
        text (str): The Slack event text

    Returns:
        Tuple[str, str]: The text without the transcript id and the transcript id
    """
    transcript_id = re.findall(r"transcript_id:\w+", text)
    transcript_id = [tid.split(":")[-1] for tid in transcript_id]

    text = re.sub(r"transcript_id:\w+", "", text)
    text = text.strip()

    return text, transcript_id


async def format_files_to_upload(
    summary: BaseSummary,
    ephemeral: bool,
) -> List[Dict[str, io.StringIO]]:
    """
    Format the summary to upload to Slack as a List of Dicts with the file name and the content.

    Args:
        summary (BaseSummary): The BaseSummary object from wordcab-python
        ephemeral (bool): The ephemeral flag

    Returns:
        List[Dict[str, io.StringIO]]: The list of files to upload with their metadata
    """
    summary_type = summary.summary_type
    summary_id = summary.summary_id

    formatted_summaries = summary.get_formatted_summaries(add_context=True)

    file_uploads: List[Dict[str, Union[str, io.StringIO]]] = []
    for key, val in formatted_summaries.items():
        if ephemeral is False:
            val = f"Transcript id: {summary.transcript_id}\n{val}"

        file_uploads.append(
            {
                "filename": f"{summary_type}_{key}_{summary_id}.txt",
                "file": io.StringIO(val),
                "title": f"{summary_type}_{key}_{summary_id}",
                "alt_text": f"Summary {summary_id} of type {summary_type} with a length of {key}.",
                "snippet_type": "text",
            }
        )

    return file_uploads


async def _get_file_names(data: JobData) -> List[str]:
    """
    Get the file names from the data.

    Args:
        data (JobData): The JobData object

    Returns:
        List[str]: The list of file names
    """
    if data.urls is not None:
        return [url.split("/")[-1] for url in data.urls]
    elif data.transcript_ids is not None:
        return [tid for tid in data.transcript_ids]
    else:
        return []


async def get_summarization_params(
    text: str, available_summary_types: List[str]
) -> Tuple[List[int], List[str], str, str, bool]:
    """
    Extract the summarization parameters from the Slack event text.

    Args:
        text (str): The Slack event text
        available_summary_types (List[str]): The list of available summary types

    Returns:
        Tuple[List[int], List[str], str, bool]: The summary length, summary type, source language, target language,
        context features and ephemeral flag
    """
    text = re.sub(r"<@\w+>", "", text)  # Remove the @user from the text

    summary_length = list({int(s) for s in re.findall(r"\d+", text) if int(s) <= 5})
    if not summary_length:
        summary_length = [1, 3, 5]

    summary_type = list({s for s in text.split() if s in available_summary_types})
    if not summary_type:
        summary_type = ["narrative"]

    source_lang = re.findall(r"source_lang:\w+", text)
    if not source_lang:
        source_lang = "en"
    elif isinstance(source_lang, list):
        source_lang = source_lang[0].split(":")[-1]

    target_lang = re.findall(r"target_lang:\w+", text)
    if not target_lang:
        target_lang = source_lang
    elif isinstance(target_lang, list):
        target_lang = target_lang[0].split(":")[-1]

    context_features = re.findall(r"context:(.*)", text)
    if not context_features:
        context_features = None
    elif isinstance(context_features, list):
        context_features = context_features[0].split()[0].split(",")

    ephemeral = re.findall(r"ephemeral:\w+", text)
    if not ephemeral:
        ephemeral = None
    elif isinstance(ephemeral, list):
        ephemeral = ephemeral[0].split(":")[-1]
        ephemeral = False if ephemeral == "false" else True

    return (
        summary_length,
        summary_type,
        source_lang,
        target_lang,
        context_features,
        ephemeral,
    )


async def get_summary(summary_id: str, api_key: str) -> BaseSummary:  # pragma: no cover
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
) -> Tuple[List[str], List[str]]:
    """
    Process the job and launch the tasks.

    Args:
        job (JobData): The job data to process including the tasks
        accepted_audio_formats (List[str]): The list of accepted audio formats
        accepted_generic_formats (List[str]): The list of accepted generic formats
        bot_token (str): The Slack bot token
        api_key (str): The Wordcab api key to use for the summarization

    Returns:
        Tuple[List[str], List[str]]: The list of job names and the list of file names
    """
    if job.transcript_ids:
        tasks = [
            _transcript_summarization_task(
                transcript_id=transcript_id,
                summary_type=summary_type,
                source_lang=job.source_lang,
                target_lang=job.target_lang,
                context_features=job.context_features,
                summary_lens=job.summary_length,
                api_key=api_key,
            )
            for summary_type in job.summary_type
            for transcript_id in job.transcript_ids
        ]
    elif job.urls:
        tasks = [
            _url_summarization_task(
                url=url,
                summary_type=summary_type,
                source_lang=job.source_lang,
                target_lang=job.target_lang,
                context_features=job.context_features,
                summary_lens=job.summary_length,
                accepted_audio_formats=accepted_audio_formats,
                accepted_generic_formats=accepted_generic_formats,
                bot_token=bot_token,
                api_key=api_key,
            )
            for summary_type in job.summary_type
            for url in job.urls
        ]

    results: List[Tuple[str, str]] = await asyncio.gather(*tasks)
    job_names, file_names = zip(*results, strict=True)

    return job_names, file_names


async def monitor_job_status(
    job_name: str, api_key: str
) -> Tuple[str, str]:  # pragma: no cover
    """
    Monitor the job status and return the summary_id when the job is done.

    Args:
        job_name (str): The job name to monitor
        api_key (str): The Wordcab api key

    Returns:
        Tuple[str, str]: The job name and the summary_id
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
            await asyncio.sleep(3)

    return job_name, job.summary_details["summary_id"]


async def _transcript_summarization_task(
    transcript_id: str,
    summary_type: str,
    source_lang: str,
    target_lang: str,
    context_features: Union[List[str], None],
    summary_lens: List[int],
    api_key: str,
) -> Tuple[str, str]:  # pragma: no cover
    """
    Launch a transcript summarization job based on the input parameters and return the job name.

    Args:
        transcript_id (str): The transcript id to summarize
        summary_type (str): The summary type to use
        source_lang (str): The source language
        target_lang (str): The target language
        context_features (Union[List[str], None]): The context features to use
        summary_lens (List[int]): The summary lengths to use
        api_key (str): The Wordcab api key

    Returns:
        Tuple[str, str]: The job name of the launched job and the transcript id
    """
    source = WordcabTranscriptSource(transcript_id=transcript_id)

    summarize_job = await asyncio.get_event_loop().run_in_executor(
        None,
        partial(
            start_summary,
            source_object=source,
            display_name="slack",
            source_lang=source_lang,
            target_lang=target_lang,
            context=context_features,
            summary_type=summary_type,
            summary_lens=summary_lens,
            tags=["slack", "slackbot"],
            api_key=api_key,
        ),
    )

    return summarize_job.job_name, transcript_id


async def _url_summarization_task(
    url: str,
    summary_type: str,
    source_lang: str,
    target_lang: str,
    context_features: Union[List[str], None],
    summary_lens: List[int],
    accepted_audio_formats: List[str],
    accepted_generic_formats: List[str],
    bot_token: str,
    api_key: str,
) -> Tuple[str, str]:  # pragma: no cover
    """
    Launch an url summarization job based on the input parameters and return the job name.

    Args:
        url (str): The url of the file to summarize
        summary_type (str): The type of summary to generate
        source_lang (str): The language of the source file
        target_lang (str): The language of the summary
        context_features (Union[List[str], None]): The list of context features to use if any else None
        summary_lens (List[int]): The list of summary lengths to generate
        accepted_audio_formats (List[str]): The list of accepted audio formats
        accepted_generic_formats (List[str]): The list of accepted generic formats
        bot_token (str): The Slack bot token
        api_key (str): The Wordcab api key

    Raises:
        Exception: If the file extension is not supported

    Returns:
        Tuple[str, str]: The job name of the launched job and the file name
    """
    filename = url.split("/")[-1]
    file_type = await _check_file_extension(
        filename=filename,
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
            target_lang=target_lang,
            context=context_features,
            summary_type=summary_type,
            summary_lens=summary_lens,
            tags=["slack", "slackbot"],
            api_key=api_key,
        ),
    )

    return summarize_job.job_name, filename
