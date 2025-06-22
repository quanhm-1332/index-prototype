import asyncio
from dataclasses import dataclass

from aio_pika import DeliveryMode, Message

from structlog.stdlib import BoundLogger
from logs import get_logger

from ._conn import RabbitMQPool


@dataclass
class RabbitMQPublisher:
    pool: RabbitMQPool
    logger: BoundLogger = get_logger("broker.rabbitmq.publisher")

    async def publish(
        self, exchange_name: str, routing_key: str, message: bytes, durable: bool = True
    ) -> None:
        async with self.pool.acquire_channel() as channel:
            exchange = await channel.get_exchange(exchange_name)
            await exchange.publish(
                Message(
                    body=message,
                    delivery_mode=(
                        DeliveryMode.PERSISTENT
                        if durable
                        else DeliveryMode.NOT_PERSISTENT
                    ),
                ),
                routing_key=routing_key,
            )
            await self.logger.adebug(
                "Message published",
                exchange=exchange_name,
                routing_key=routing_key,
                message_length=len(message),
            )
