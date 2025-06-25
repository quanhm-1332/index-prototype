from dataclasses import dataclass
import io
from functools import wraps

from structlog.stdlib import BoundLogger
from logs import get_logger

from storage import ObjectStorage
from tasks import TaskController, TaskUpdate, TaskStatus
from broker import (
    RabbitMQPublisher,
    AbstractIncomingMessage,
    TaskMessage,
    RabbitMQSubscriber,
    start_subscriber,
)
from .builder import IBuilder


@dataclass
class Processor:
    storage: ObjectStorage
    task_controller: TaskController
    rabbitmq_publisher: RabbitMQPublisher
    rabbitmq_subscriber: RabbitMQSubscriber
    builder: IBuilder
    logger: BoundLogger = get_logger("worker.processor")

    async def _process_message(self, task_msg: TaskMessage) -> bool:
        if task_msg.resource_url is None:
            await self.logger.aerror(
                "Task message has no resource URL",
                task_id=task_msg.id,
                task_name=task_msg.task_name,
                resource_url=task_msg.resource_url,
            )
            return False

        # Process the task message (e.g., download, analyze, etc.)
        # This is a placeholder for actual processing logic
        await self.builder.build(task_msg.resource_url)

        return True

    async def callback(self, msg: AbstractIncomingMessage) -> bool:
        try:
            task_msg = TaskMessage.model_validate_json(msg.body)
            result = await self._process_message(task_msg)
            if result:
                await self.task_controller.update(
                    TaskUpdate(
                        id=task_msg.id,
                        status=TaskStatus.COMPLETED,
                        phase=task_msg.task_name,
                    )
                )
            else:
                await self.task_controller.update(
                    TaskUpdate(
                        id=task_msg.id,
                        status=TaskStatus.FAILED,
                        phase=task_msg.task_name,
                    )
                )
            return result
        except Exception as e:
            await self.logger.aexception(
                "Error processing message",
                error=str(e),
                body=msg.body.decode("utf-8"),
            )
            return False

    async def process(self):
        """
        Start the message processing loop.
        """
        coro = await self.rabbitmq_subscriber.subscribe(
            callback=self.callback,
        )
        await self.logger.ainfo("Processor started and listening for messages")
        await start_subscriber(coro)
