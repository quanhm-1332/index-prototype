from typing import Any
from pydantic import BaseModel


class TaskMessage(BaseModel):
    id: str
    from_queue: str
    to_queue: str
    resource_url: str | None
    metadata: dict[str, Any]
