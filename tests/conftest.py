# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Conftest for the wordcab_slack package tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_delete_job():
    """Mock the delete_job function."""
    return AsyncMock(wraps=MagicMock(name="delete_job"))
