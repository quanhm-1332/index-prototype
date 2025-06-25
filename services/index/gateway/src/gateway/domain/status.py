from tasks import TaskController


async def poll_task_status(controller: TaskController, task_id: str):
    return await controller.get(task_id)
