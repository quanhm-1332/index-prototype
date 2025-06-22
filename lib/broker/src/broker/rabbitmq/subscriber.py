import asyncio
from dataclasses import dataclass
import signal

from aio_pika.abc import AbstractIncomingMessage

from structlog.stdlib import BoundLogger
from logs import get_logger

from ._conn import RabbitMQPool


@dataclass
class RabbitMQSubscriber:
    pool: RabbitMQPool
    logger: BoundLogger = get_logger("broker.rabbitmq.subscriber")

    async def subscribe(self, queue_name: str, routing_key: str):
        async with self.pool.acquire_channel() as channel:
            await channel.set_qos(prefetch_count=1)
            queue = await channel.get_queue(queue_name)

            await self.logger.ainfo(
                "Subscribed to queue",
                queue=queue_name,
                routing_key=routing_key,
            )

            async with queue.iterator() as queue_iter:
                async for msg in queue_iter:
                    async with msg.process():
                        yield msg


async def run(coro, logger: BoundLogger = get_logger("broker.rabbitmq.runner")) -> None:

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown_event.set)
    loop.add_signal_handler(signal.SIGTERM, shutdown_event.set)

    _task = asyncio.create_task(coro)
    await shutdown_event.wait()
    _task.cancel()
    try:
        await _task
        await logger.ainfo("Worker stopped gracefully")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        await logger.aexception("Worker error")
