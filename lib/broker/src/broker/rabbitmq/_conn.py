from dataclasses import dataclass
from contextlib import asynccontextmanager

from aio_pika import ExchangeType
from aio_pika.abc import AbstractChannel, AbstractRobustConnection
from aio_pika.pool import Pool
from aio_pika.robust_connection import connect_robust

from structlog.stdlib import BoundLogger
from logs import get_logger

from .settings import RabbitMQSettings


@dataclass
class RabbitMQPool:
    settings: RabbitMQSettings
    logger: BoundLogger = get_logger("broker.rabbitmq.pool")

    def __post_init__(self):
        async def create_connection() -> AbstractRobustConnection:
            return await connect_robust(
                host=self.settings.host,
                port=self.settings.port,
                login=self.settings.username,
                password=self.settings.password.get_secret_value(),
            )

        self._pool: Pool[AbstractRobustConnection] = Pool(
            create_connection,
            max_size=self.settings.max_conn,
        )

        async def create_channel() -> AbstractChannel:
            async with self._pool.acquire() as connection:
                return await connection.channel()

        self._channel_pool: Pool[AbstractChannel] = Pool(
            create_channel, max_size=self.settings.max_channel
        )

        self.logger.info(
            "RabbitMQ connection initialized",
            host=self.settings.host,
            port=self.settings.port,
            max_conn=self.settings.max_conn,
            max_channel=self.settings.max_channel,
        )

    @asynccontextmanager
    async def acquire_connection(self):
        async with self._pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def acquire_channel(self):
        async with self._channel_pool.acquire() as channel:
            yield channel

    async def bind(self, exchange_name: str, queue_name: str, routing_key: str):
        async with self.acquire_channel() as channel:
            exchange = await channel.declare_exchange(
                exchange_name,
                type=ExchangeType.TOPIC,
                # passive=True,
                durable=True,
            )
            queue = await channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key)
            await self.logger.ainfo(
                "Queue bound to exchange",
                exchange=exchange_name,
                queue=queue_name,
                routing_key=routing_key,
            )
