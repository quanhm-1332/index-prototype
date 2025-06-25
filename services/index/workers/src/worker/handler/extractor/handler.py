from dataclasses import dataclass
from structlog.stdlib import BoundLogger
from pydantic import ValidationError, AnyUrl

from broker import AbstractIncomingMessage, TaskMessage, RabbitMQPublisher
from tasks import TaskController
from storage import ObjectStorage

from .extractor import extract_entities
from .._interface import IHandler, ResourceInvalid, HandlerException
from ..utils import build_resource_url


@dataclass
class ExtractorHandler(IHandler):
    async def handle(self, task_id: str, resources_url: str) -> tuple[bytes, str]:
        try:
            _url = AnyUrl(resources_url)
        except Exception as e:
            raise ResourceInvalid(resources_url, "Invalid resource format") from e

        match (_url.scheme, _url.host):
            case ("minio", "arxiv"):
                try:
                    resource_content = await extract_entities(
                        resource_url=_url,
                        storage=self.storage,
                    )
                except ValueError as e:
                    raise ResourceInvalid(resources_url, str(e))
                return (
                    resource_content,
                    build_resource_url(
                        "minio",
                        _url.host,
                        self.bucket_name,
                        self.object_name,
                        task_id,
                    ),
                )
            case _:
                raise ResourceInvalid(
                    resources_url,
                    f"Unsupported resource scheme and host: {_url.scheme}, {_url.host}",
                )
