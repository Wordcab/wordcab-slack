# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests for the _summarization_task function in utils.py file."""

import pytest
import pytest_mock
from unittest.mock import AsyncMock

from wordcab_slack.utils import _summarization_task


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, summary_type, source_lang, summary_lens, expected_raised_exception",
    [
        (
            "https://example.com/image.png",
            "narrative",
            "en",
            [1, 3, 5],
            Exception,
        ),
        (
            "https://example.com/transcript.pdf",
            "conversational",
            "en",
            [1, 3, 5],
            Exception,
        )
    ]
)
async def test_summarization_task_with_invalid_file(
    mocker: pytest_mock.MockFixture,
    url: str,
    summary_type: str,
    source_lang: str,
    summary_lens: list,
    expected_raised_exception: Exception,
) -> None:
    """Test the _summarization_task function with an invalid file extension."""
    with pytest.raises(expected_raised_exception):
        mock_start_summary = AsyncMock()
        mocker.patch("wordcab.api.start_summary", mock_start_summary)

        await _summarization_task(
            url=url,
            summary_type=summary_type,
            source_lang=source_lang,
            summary_lens=summary_lens,
            accepted_audio_formats=[".mp3", ".wav"],
            accepted_generic_formats=[".txt"],
            bot_token="my_bot_token",
            api_key="my_api_key",
        )
