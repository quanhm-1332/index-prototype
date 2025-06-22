from typing import Annotated, Literal
from pydantic import BaseModel, Discriminator
from enum import Enum


class ArxivMetadata:
    kind: Literal["arxiv"] = "arxiv"
    max_results: int | None = None


class WikipediaMetadata:
    kind: Literal["wikipedia"] = "wikipedia"


RequestMetadata = Annotated[ArxivMetadata | WikipediaMetadata, Discriminator("kind")]


class IndexRequest(BaseModel):
    query: str
    metadata: RequestMetadata
