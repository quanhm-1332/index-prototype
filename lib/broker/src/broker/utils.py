import asyncio
import signal

from structlog.stdlib import BoundLogger
from logs import get_logger


async def start_subscriber(
    coro, logger: BoundLogger = get_logger("broker.rabbitmq.runner")
) -> None:

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
    except Exception:
        await logger.aexception("Worker error")
