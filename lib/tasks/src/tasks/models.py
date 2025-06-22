from datetime import datetime
from pydantic import BaseModel


class TaskBase(BaseModel):

    status: int  # Using int to represent TaskStatus
    department: str
    phase: str


class TaskCreate(TaskBase):
    id: str


class Task(TaskBase):
    id: str
    createAt: datetime
    updateAt: datetime
