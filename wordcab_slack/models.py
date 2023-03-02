# Copyright (c) 2023, The Wordcab team. All rights reserved.

from typing import List, Optional

from pydantic import BaseModel, root_validator


class SummaryData(BaseModel):
    """Summary data for launching the summary jobs"""
    summary_type: List[str]
    summary_length: List[int]
    target_lang: str
    delete_job: bool
    urls: List[str]
    msg_id: str
    num_tasks: Optional[int] = None
    
    @root_validator
    def compute_num_tasks(cls, values):
        """Compute the number of tasks to be launched"""
        num_tasks = len(values["urls"]) * len(values["summary_type"])
        values["num_tasks"] = num_tasks
        return values
