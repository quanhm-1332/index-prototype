from fastapi import APIRouter
from fastapi import Response

from ..models import IndexRequest

router = APIRouter(prefix="/arxiv", tags=["arxiv"])


@router.post("/index")
async def index_arxiv(request: IndexRequest):
    if request.metadata.kind != "arxiv":
        return Response(status_code=400, content="Invalid metadata kind")

    return Response(status_code=202, content="Indexing request accepted")
