# Copyright (c) 2023, The Wordcab team. All rights reserved.
# flake8: noqa: S106
"""Tests for the _launch_job_tasks function in utils.py file."""

from unittest.mock import AsyncMock

import pytest
import pytest_mock

from wordcab_slack.models import JobData
from wordcab_slack.utils import _launch_job_tasks


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "urls, summary_type, source_lang, summary_length, expected_tasks",
    [
        (
            ["https://example.com/audio.mp3", "https://example.com/transcript.txt"],
            ["narrative", "conversational"],
            "en",
            [1, 3, 5],
            [
                [
                    "https://example.com/audio.mp3",
                    "narrative",
                    "en",
                    "en",
                    None,
                    [1, 3, 5],
                    [".mp3", ".wav"],
                    [".txt"],
                    "my_bot_token",  # noqa: S106
                    "my_api_key",
                ],
                [
                    "https://example.com/transcript.txt",
                    "narrative",
                    "en",
                    "en",
                    None,
                    [1, 3, 5],
                    [".mp3", ".wav"],
                    [".txt"],
                    "my_bot_token",  # noqa: S106
                    "my_api_key",
                ],
                [
                    "https://example.com/audio.mp3",
                    "conversational",
                    "en",
                    "en",
                    None,
                    [1, 3, 5],
                    [".mp3", ".wav"],
                    [".txt"],
                    "my_bot_token",  # noqa: S106
                    "my_api_key",
                ],
                [
                    "https://example.com/transcript.txt",
                    "conversational",
                    "en",
                    "en",
                    None,
                    [1, 3, 5],
                    [".mp3", ".wav"],
                    [".txt"],
                    "my_bot_token",  # noqa: S106
                    "my_api_key",
                ],
            ],
        )
    ],
)
async def test_launch_job_tasks(
    mocker: pytest_mock.MockFixture,
    urls: list,
    summary_type: list,
    source_lang: str,
    summary_length: list,
    expected_tasks: list,
) -> None:
    """Test the _launch_job_tasks function."""
    job = JobData(
        summary_length=summary_length,
        summary_type=summary_type,
        source_lang=source_lang,
        target_lang=source_lang,
        context_features=None,
        urls=urls,
        msg_id="123",
    )

    mock_task = AsyncMock(return_value=tuple(f"{job.msg_id}", urls[0].split("/")[-1]))
    mocker.patch("wordcab_slack.utils._url_summarization_task", mock_task)

    result = await _launch_job_tasks(
        job,
        accepted_audio_formats=[".mp3", ".wav"],
        accepted_generic_formats=[".txt"],
        bot_token="my_bot_token",  # noqa: S106
        api_key="my_api_key",
    )
    job_names, file_names = result

    assert len(job_names) == len(expected_tasks) == len(file_names)
    for i in range(len(expected_tasks)):
        assert job_names[i] == f"{job.msg_id}"
        assert file_names[i] == urls[0].split("/")[-1]
        assert list(mock_task.call_args_list[i][1].values()) == expected_tasks[i]
        assert mock_task.await_count == len(expected_tasks)
