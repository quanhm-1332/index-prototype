import importlib
import requests

from logs import get_logger, setup_logging
from db import PostgresClient
from tasks import Pipeline, PostgreSQLController
from broker import RabbitMQPublisher, RabbitMQPool, RabbitMQSubscriber
from storage import MinIOStorage
from .settings import get_settings
from .handler import IHandler, HandlerRegistry
from .processor import Processor

setup_logging()


async def run() -> None:
    settings = get_settings()

    logger = get_logger("worker.main")

    pool = RabbitMQPool(settings=settings.rabbitmq)
    publisher = RabbitMQPublisher(pool)
    controller = PostgreSQLController(await PostgresClient.init(settings.postgre))

    storage = MinIOStorage(settings=settings.minio)

    response = requests.get(f"{settings.master.url}/pipeline/config")
    if response.status_code != 200:
        logger.error(
            "Failed to fetch pipeline configuration",
            status_code=response.status_code,
            url=settings.master.url,
        )
        return

    pipeline_config = Pipeline.model_validate_json(response.content)

    handler_register = HandlerRegistry()

    subscriber = RabbitMQSubscriber(
        pool=pool,
        queue_name=pipeline_config.backlog_queue_name,
    )

    for task_name, task_info in pipeline_config.pipeline.items():
        try:
            module = importlib.import_module(f".{task_info.handler}", "worker")
            handler_class: type[IHandler] = getattr(module, "Handler")
            handler_instance = handler_class(
                publisher=publisher,
                controller=controller,
                storage=storage,
                logger=get_logger(f"worker.handler.{task_name}"),
                task_name=task_name,
                bucket_name=task_info.bucket_name,
                object_name=task_info.object_name,
                exchange_name=pipeline_config.exchange_name,
                routing_key=task_info.routing_key,
                from_queue=pipeline_config.backlog_queue_name,
                to_queue=(
                    pipeline_config.builder_queue_name
                    if task_info.last
                    else pipeline_config.backlog_queue_name
                ),
                next_task_name=task_info.next_task_name,
                **task_info.args,
            )
            await pool.bind(
                handler_instance.exchange_name,
                handler_instance.to_queue,
                handler_instance.routing_key,
            )

            handler_register.register(task_name, handler_instance)

            logger.info("Handler loaded successfully", task_name=task_name)
        except (ImportError, AttributeError):
            logger.error(
                "Failed to load handler",
                task_name=task_name,
                **task_info.model_dump(),
            )
            return
    processor = Processor(
        storage=storage,
        task_controller=controller,
        rabbitmq_publisher=publisher,
        rabbitmq_subscriber=subscriber,
        handlers=handler_register,
        logger=get_logger("worker.processor"),
    )
    logger.info("Pipeline configuration fetched successfully", pipeline=pipeline_config)

    await processor.process()


def main():
    import asyncio

    asyncio.run(run())
