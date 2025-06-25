import yaml
from fastapi import APIRouter, Depends
from tasks import Pipeline
from ..dependencies.config import load_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/config")
async def get_pipeline_config(pipeline: Pipeline = Depends(load_pipeline)):
    """
    Fetch the pipeline configuration from the YAML file.
    """
    return pipeline
