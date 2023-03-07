# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""Tests mocks for the wordcab_slack package."""

from asyncio import AbstractEventLoop


class MockEventLoop(AbstractEventLoop):
    """Mock event loop for testing."""

    def run_in_executor(self, executor, func, *args):
        """Mock run_in_executor method."""
        return executor.submit(func, *args)
