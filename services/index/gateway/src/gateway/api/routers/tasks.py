from os import pipe
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response
from tasks import TaskController, Pipeline, TaskStatus
from ...application.status import StatusPolling
from ..models import TaskStatusResponse

from ..dependencies.resources import get_task_controller
from ..dependencies.config import load_pipeline

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/status/{task_id}")
async def status_arxiv(
    task_id: Annotated[str, Path(description="The task ID to check status for")],
    task_controller: Annotated[TaskController, Depends(get_task_controller)],
    pipeline: Annotated[Pipeline, Depends(load_pipeline)],
):
    status_polling = StatusPolling(controller=task_controller)

    task_status = await status_polling.poll(task_id)
    if task_status is None:
        return Response(status_code=404, content="Task not found")

    progress = {}
    pipeline_steps = list(pipeline.pipeline)
    pipeline_steps.append(
        "builder"
    )  # Ensure 'builder' is included in the pipeline steps
    if task_status.phase in pipeline_steps:
        match task_status.status:
            case TaskStatus.PENDING:
                # If the task is pending, we assume it has not started yet
                for order, phase in enumerate(pipeline_steps):
                    progress[phase] = {
                        "order": order,
                        "status": "PENDING",
                    }
            case TaskStatus.IN_PROGRESS:
                ptr = pipeline_steps.index(task_status.phase)
                for order, phase in enumerate(pipeline_steps):
                    if order < ptr:
                        progress[phase] = {
                            "order": order,
                            "status": "COMPLETED",
                        }
                    elif order == ptr:
                        progress[phase] = {
                            "order": order,
                            "status": "IN_PROGRESS",
                        }
                    else:

                        progress[phase] = {
                            "order": order,
                            "status": "PENDING",
                        }
            case TaskStatus.COMPLETED:
                for order, phase in enumerate(pipeline_steps):
                    progress[phase] = {
                        "order": order,
                        "status": "COMPLETED",
                    }
    resp = TaskStatusResponse(
        task_id=task_status.id,
        status=task_status.status.name,
        phase=task_status.phase,
        progress=progress,
    )

    return resp
