from datetime import datetime
from typing import Any
from pydantic import BaseModel
from enum import Enum


class TaskStatus(int, Enum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


class TaskUpdate(BaseModel):
    id: str
    status: TaskStatus | None = None
    department: str | None = None
    phase: str | None = None


class TaskCreate(BaseModel):
    id: str
    status: TaskStatus
    department: str
    phase: str


class Task(BaseModel):
    id: str
    status: TaskStatus
    department: str
    phase: str
    createAt: datetime
    updateAt: datetime


class TaskInfo(BaseModel):
    handler: str

    task_name: str
    next_task_name: str

    first: bool = False
    last: bool = False

    routing_key: str

    bucket_name: str
    object_name: str

    args: dict[str, Any] = {}


class Pipeline(BaseModel):
    pipeline: dict[str, TaskInfo]
    exchange_name: str
    backlog_queue_name: str
    builder_queue_name: str
