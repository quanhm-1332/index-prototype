import requests

from neo4j import AsyncGraphDatabase

from logs import get_logger, setup_logging
from db import PostgresClient
from tasks import Pipeline, PostgreSQLController
from broker import RabbitMQPublisher, RabbitMQPool, RabbitMQSubscriber
from storage import MinIOStorage
from .settings import get_settings
from .builder import Neo4jBuilder
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

    driver = AsyncGraphDatabase.driver(
        settings.neo4j.dsn.encoded_string(), auth=settings.neo4j.dsn.get_auth()
    )

    builder = Neo4jBuilder(
        storage=storage, logger=get_logger("builder.neo4j"), driver=driver
    )  # type: ignore

    subscriber = RabbitMQSubscriber(
        pool=pool,
        queue_name=pipeline_config.builder_queue_name,
    )

    processor = Processor(
        storage=storage,
        task_controller=controller,
        rabbitmq_publisher=publisher,
        rabbitmq_subscriber=subscriber,
        builder=builder,
        logger=get_logger("builder.processor"),
    )
    logger.info("Pipeline configuration fetched successfully", pipeline=pipeline_config)

    await processor.process()


def main():
    import asyncio

    asyncio.run(run())
