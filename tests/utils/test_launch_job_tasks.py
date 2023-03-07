# Copyright (c) 2023, The Wordcab team. All rights reserved.
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
    # flake8: noqa: S106
    job = JobData(
        summary_length=summary_length,
        summary_type=summary_type,
        source_lang=source_lang,
        delete_job=True,
        urls=urls,
        msg_id="123",
    )

    mock_task = AsyncMock(return_value=f"{job.msg_id}")
    mocker.patch("wordcab_slack.utils._summarization_task", mock_task)

    job_names = await _launch_job_tasks(
        job,
        accepted_audio_formats=[".mp3", ".wav"],
        accepted_generic_formats=[".txt"],
        bot_token="my_bot_token",
        api_key="my_api_key",
    )

    assert len(job_names) == len(expected_tasks)
    for i in range(len(expected_tasks)):
        assert job_names[i] == f"{job.msg_id}"
        assert list(mock_task.call_args_list[i][1].values()) == expected_tasks[i]
        assert mock_task.await_count == len(expected_tasks)
