# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Conftest for the wordcab_slack package tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_delete_job():
    return AsyncMock(wraps=MagicMock(name="delete_job"))
