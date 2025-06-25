from dataclasses import dataclass

from sqlalchemy import insert, update
from structlog.stdlib import BoundLogger

from logs import get_logger
from db import PostgresClient

from ..proto import TaskController
from ..models import TaskCreate, Task, TaskUpdate

from .schema import Task as TaskSchema


@dataclass
class PostgreSQLController(TaskController):
    client: PostgresClient
    logger: BoundLogger = get_logger("tasks.controller.pg")

    async def create(self, task: TaskCreate):
        """
        Create a new task in the PostgreSQL database.
        """
        async with self.client.get_session() as session:
            async with session.begin():
                stmt = insert(TaskSchema).values(
                    **task.model_dump(exclude_none=True, exclude_unset=True)
                )
                await session.execute(stmt)
                await self.logger.ainfo("Task created")

    async def update(self, task: TaskUpdate):
        """
        Update an existing task in the PostgreSQL database.
        """
        async with self.client.get_session() as session:
            async with session.begin():
                values = task.model_dump(
                    exclude={"id"}, exclude_unset=True, exclude_none=True
                )
                stmt = (
                    update(TaskSchema).where(TaskSchema.id == task.id).values(**values)
                )
                await session.execute(stmt)
                await self.logger.ainfo("Task updated", task_id=task.id, **values)

    async def get(self, task_id: str) -> Task | None:
        async with self.client.get_session() as session:
            async with session.begin():
                result = await session.get(
                    TaskSchema, task_id
                )  # Ensure the table is created
                return (
                    Task.model_validate(result, from_attributes=True)
                    if result
                    else None
                )
