from .arxiv import router as arxiv_router
from .tasks import router as tasks_router
from .pipeline import router as pipeline_router

__all__ = [
    "arxiv_router",
    "tasks_router",
    "pipeline_router",
]
