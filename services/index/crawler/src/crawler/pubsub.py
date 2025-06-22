import io
import json

from pydantic import ValidationError
from structlog.stdlib import BoundLogger

from logs import get_logger
from broker import RabbitMQSubscriber, RabbitMQPublisher, RabbitMQPool, TaskMessage
from db import PostgresClient
from tasks import TaskController, TaskCreate, TaskStatus, PostgreSQLController
from storage import (
    MinioSettings,
    MinIOStorage,
    ObjectStorage,
    ObjectStorageOptionalPutArgs,
)

from .settings import CrawlerSettings
from .loader import query_arxiv


async def pubsub(
    settings: CrawlerSettings, logger: BoundLogger = get_logger("arxiv.crawler.pubsub")
) -> None:
    """
    Initialize RabbitMQ publisher and subscriber.
    """

    controller = PostgreSQLController(
        await PostgresClient.init(settings=settings.postgre)
    )
    storage = MinIOStorage(settings=settings.minio)

    pool = RabbitMQPool(settings=settings.rabbitmq)
    await pool.bind(
        settings.subscriber_connector.exchange_name,
        settings.subscriber_connector.queue_name,
        settings.subscriber_connector.routing_key,
    )

    await pool.bind(
        settings.publisher_connector.exchange_name,
        settings.publisher_connector.queue_name,
        settings.publisher_connector.routing_key,
    )

    publisher = RabbitMQPublisher(pool)
    subscriber = RabbitMQSubscriber(pool)

    async for msg in subscriber.subscribe(
        settings.subscriber_connector.queue_name,
        settings.subscriber_connector.routing_key,
    ):
        try:
            task_msg = TaskMessage.model_validate_json(msg.body)
            if task_msg.resource_url is None:
                await logger.aerror(
                    "Task message has no resource URL",
                    body=msg.body.decode("utf-8"),
                )
                await msg.reject(requeue=False)
                continue
            scheme, query = task_msg.resource_url.split("://")

            match scheme:
                case "arxiv":
                    resource_url = await _handle_arxiv_query(
                        query=query,
                        logger=logger,
                        task_msg=task_msg,
                        bucket_name=settings.subscriber_connector.queue_name.replace(
                            ".", "_"
                        ),
                        controller=controller,
                        storage=storage,
                    )

                    new_task_msg = TaskMessage(
                        id=task_msg.id,
                        from_queue=settings.subscriber_connector.queue_name,
                        to_queue=settings.publisher_connector.queue_name,
                        resource_url=resource_url,
                        metadata=task_msg.metadata,
                    )

                    await publisher.publish(
                        exchange_name=settings.publisher_connector.exchange_name,
                        routing_key=settings.publisher_connector.routing_key,
                        message=new_task_msg.model_dump_json(exclude_none=True).encode(
                            "utf-8"
                        ),
                    )

                    await msg.ack()

                case _:
                    await logger.aerror(
                        "Invalid resource URL scheme",
                        body=msg.body.decode("utf-8"),
                        scheme=scheme,
                    )
                    await msg.reject(requeue=False)
                    break

        except ValidationError as e:
            await logger.aexception(
                "Invalid message format",
                body=msg.body.decode("utf-8"),
            )
            await msg.reject(requeue=False)


async def _handle_arxiv_query(
    query: str,
    logger: BoundLogger,
    task_msg: TaskMessage,
    bucket_name: str,
    controller: TaskController,
    storage: ObjectStorage,
):
    """
    Handle the arXiv query and publish results.
    """
    await logger.ainfo(
        "Processing task message",
        task_id=task_msg.id,
        resource_url=task_msg.resource_url,
    )

    query, max_results = query.split("?")

    if not max_results.isdigit():
        max_results = 1

    if int(max_results) <= 0:
        max_results = 1

    docs = await query_arxiv(
        query,
        max_results=int(max_results),
        logger=logger,
    )

    _docs_object = {"docs": docs}

    _docs_json = json.dumps(_docs_object, ensure_ascii=False)
    _docs_bytes = _docs_json.encode("utf-8")

    await storage.put_file(
        bucket_name=bucket_name,
        object_name=f"{task_msg.id}_{query}.json",
        data=io.BytesIO(_docs_bytes),
    )

    await logger.ainfo(
        "Published results to storage",
        task_id=task_msg.id,
        bucket_name=bucket_name,
    )

    await controller.create(
        TaskCreate(
            id=task_msg.id,
            status=TaskStatus.IN_PROGRESS,
            department="arxiv",
            phase="crawler",
        )
    )
    await logger.ainfo(
        "Task status updated",
        task_id=task_msg.id,
        status=TaskStatus.IN_PROGRESS,
    )

    return f"storage://{bucket_name}/{task_msg.id}_{query}.json"
