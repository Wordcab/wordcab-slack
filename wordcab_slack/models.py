# Copyright (c) 2023, The Wordcab team. All rights reserved.

from typing import List, Optional

from pydantic import BaseModel


class JobData(BaseModel):
    """Summary data for launching the summary jobs"""

    summary_length: List[int]
    summary_type: List[str]
    source_lang: str
    delete_job: bool
    urls: List[str]
    msg_id: str
    num_tasks: Optional[int] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.num_tasks = len(self.urls) * len(self.summary_type)
