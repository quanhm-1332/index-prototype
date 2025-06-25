from dataclasses import dataclass

from tasks import TaskController
from ..domain.status import poll_task_status


@dataclass
class StatusPolling:
    controller: TaskController

    async def poll(self, task_id: str):
        return await poll_task_status(self.controller, task_id)
