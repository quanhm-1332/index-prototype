from typing import Any
from pydantic import BaseModel


class TaskMessage(BaseModel):
    id: str
    task_name: str
    resource_url: str | None
    metadata: dict[str, Any]
