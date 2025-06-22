from pydantic import ValidationError
from structlog.stdlib import BoundLogger

from logs import get_logger
from broker import RabbitMQSubscriber, RabbitMQPublisher, RabbitMQPool, TaskMessage

from .settings import CrawlerSettings


async def pubsub(
    settings: CrawlerSettings, logger: BoundLogger = get_logger("arxiv.crawler.pubsub")
) -> None:
    """
    Initialize RabbitMQ publisher and subscriber.
    """
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

        except ValidationError as e:
            await logger.aexception(
                "Invalid message format",
                body=msg.body.decode("utf-8"),
            )
            await msg.reject(requeue=False)

    # Example of publishing a message
    await publisher.publish(
        "test_exchange", "test_routing_key", {"message": "Hello, World!"}
    )

    # Example of subscribing to a queue
    async for message in subscriber.subscribe("test_queue"):
        print(f"Received message: {message}")
