from typing import Annotated
from fastapi import APIRouter
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi import Path
from fastapi import Depends

from broker import RabbitMQPublisher
from tasks import TaskController, Pipeline


from ...application.status import StatusPolling
from ...application.arxiv import ArxivIndexer

from ..models import IndexRequest, TaskStatusResponse, Progress
from ..dependencies.resources import get_publisher, get_task_controller
from ..dependencies.config import load_pipeline

from ...settings import Settings, get_settings

router = APIRouter(prefix="/arxiv", tags=["arxiv"])


@router.post("/index")
async def index_arxiv(
    request: IndexRequest,
    controller: Annotated[TaskController, Depends(get_task_controller)],
    publisher: Annotated[RabbitMQPublisher, Depends(get_publisher)],
    pipeline: Annotated[Pipeline, Depends(load_pipeline)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    if request.metadata.kind != "arxiv":
        return Response(status_code=400, content="Invalid metadata kind")

    indexer = ArxivIndexer(controller=controller, publisher=publisher)

    first_task_name = None

    for k, v in pipeline.pipeline.items():
        if v.first:
            first_task_name = k
            break

    if not first_task_name:
        raise ValueError("No first task found in the pipeline configuration")

    task_id = await indexer.run(
        query=request.query,
        max_results=request.metadata.max_results,
        exchange_name="gateway",
        routing_key="gateway.#",
        task_name=first_task_name,
    )

    return JSONResponse(
        content={
            "task_id": task_id,
            "pipeline": list(pipeline.pipeline.keys()) + ["builder"],
        },
        status_code=202,
    )
