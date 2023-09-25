# Copyright (c) 2023, The Wordcab team. All rights reserved.
"""API models for the wordcab_slack package."""

from typing import List, Union

from pydantic import BaseModel


class JobData(BaseModel):
    """Summary data for launching the summary jobs."""

    summary_length: List[int]
    summary_type: List[str]
    source_lang: str
    target_lang: str
    context_features: Union[List[str], None]
    urls: Union[List[str], None] = None
    transcript_ids: Union[List[str], None] = None
    msg_id: str
    num_tasks: Union[int, None] = None

    def __init__(self, **data):
        """Set the number of tasks to be run."""
        super().__init__(**data)

        if self.urls:
            self.num_tasks = len(self.urls) * len(self.summary_type)
        elif self.transcript_ids:
            self.num_tasks = len(self.transcript_ids) * len(self.summary_type)
        else:
            raise ValueError("Either urls or transcript_ids must be provided.")
