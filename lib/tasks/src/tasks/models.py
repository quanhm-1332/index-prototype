from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class TaskStatus(int, Enum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


class TaskBase(BaseModel):

    status: TaskStatus
    department: str
    phase: str


class TaskCreate(TaskBase):
    id: str


class Task(TaskBase):
    id: str
    createAt: datetime
    updateAt: datetime
