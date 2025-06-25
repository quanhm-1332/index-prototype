from collections.abc import Awaitable, Callable
from aio_pika.abc import AbstractIncomingMessage

SubcriberCallback = Callable[[AbstractIncomingMessage], Awaitable[bool]]
