from typing import Annotated, Literal
from pydantic import BaseModel, Field

from db import PostgresClient
from broker import RabbitMQPool

from ..base import ArbitraryBaseModel as BaseModel


class Resources(BaseModel):
    db: PostgresClient
    broker: RabbitMQPool


class ArxivMetadata(BaseModel):
    kind: Literal["arxiv"]
    max_results: int | None = None


class WikipediaMetadata(BaseModel):
    kind: Literal["wikipedia"]
    max_results: int | None = None


RequestMetadata = Annotated[
    ArxivMetadata | WikipediaMetadata, Field(discriminator="kind")
]


class IndexRequest(BaseModel):
    query: str
    metadata: RequestMetadata


class Progress(BaseModel):
    order: int
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    phase: str
    progress: dict[str, Progress] | None = None
