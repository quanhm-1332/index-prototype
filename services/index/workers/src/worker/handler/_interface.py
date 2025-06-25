from typing import Protocol
from dataclasses import dataclass, field

from structlog.stdlib import BoundLogger
from broker import RabbitMQPublisher
from tasks import TaskController
from storage import ObjectStorage
from logs import get_logger


@dataclass
class IHandler(Protocol):
    publisher: RabbitMQPublisher
    controller: TaskController
    storage: ObjectStorage
    logger: BoundLogger

    task_name: str
    bucket_name: str
    object_name: str

    exchange_name: str
    routing_key: str

    from_queue: str
    to_queue: str

    next_task_name: str

    async def handle(self, task_id: str, resources_url: str) -> tuple[bytes, str]: ...


@dataclass
class HandlerRegistry:
    _handlers: dict[str, IHandler] = field(default_factory=dict)

    def register(self, op: str, handler: IHandler) -> None:
        if op in self._handlers:
            raise ValueError(f"Handler for operation '{op}' is already registered.")
        self._handlers[op] = handler

    def get_handler(self, op: str) -> IHandler | None:
        if op not in self._handlers:
            return None
        return self._handlers[op]


class ResourceInvalid(Exception):
    def __init__(self, resource: str, message: str):
        super().__init__(message)
        self.resource = resource


class HandlerException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
