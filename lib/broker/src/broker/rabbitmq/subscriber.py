import asyncio
from dataclasses import dataclass
import signal
from aio_pika.abc import AbstractIncomingMessage

from structlog.stdlib import BoundLogger
from logs import get_logger

from ._conn import RabbitMQPool
from .types import SubcriberCallback


@dataclass
class RabbitMQSubscriber:
    pool: RabbitMQPool
    queue_name: str
    logger: BoundLogger = get_logger("broker.rabbitmq.subscriber")

    async def subscribe(self, callback: SubcriberCallback):
        async with self.pool.acquire_channel() as channel:
            await channel.set_qos(prefetch_count=1)
            queue = await channel.get_queue(self.queue_name)

            await self.logger.ainfo(
                "Subscribed to queue",
                queue=self.queue_name,
            )

            async def callback_wrapper(msg: AbstractIncomingMessage):
                async with msg.process(ignore_processed=True):
                    ret = await callback(msg)
                    if ret:
                        await msg.ack()
                    else:
                        await msg.reject(requeue=False)

            return queue.consume(callback_wrapper)
