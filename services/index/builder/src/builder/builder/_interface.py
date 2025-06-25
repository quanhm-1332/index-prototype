from typing import Protocol
from dataclasses import dataclass

from storage import ObjectStorage
from structlog.stdlib import BoundLogger


@dataclass
class IBuilder(Protocol):
    storage: ObjectStorage
    logger: BoundLogger

    async def build(self, resources_url: str) -> None: ...


class ResourceInvalid(Exception):
    def __init__(self, resource: str, message: str):
        super().__init__(message)
        self.resource = resource
