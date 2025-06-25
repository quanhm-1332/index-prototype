from dataclasses import dataclass
import io

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
from .handler import HandlerRegistry
from .handler.utils import build_resource_url


@dataclass
class Processor:
    storage: ObjectStorage
    task_controller: TaskController
    rabbitmq_publisher: RabbitMQPublisher
    rabbitmq_subscriber: RabbitMQSubscriber
    handlers: HandlerRegistry
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
        handler = self.handlers.get_handler(task_msg.task_name)
        if not handler:
            await self.logger.aerror(
                "No handler found for task",
                task_name=task_msg.task_name,
                task_id=task_msg.id,
                resource_url=task_msg.resource_url,
            )
            return False
        processed_data, new_resource_url = await handler.handle(
            task_msg.id, task_msg.resource_url
        )

        await self.storage.put_file(
            handler.bucket_name,
            f"{task_msg.id}_{handler.object_name}",
            io.BytesIO(processed_data),
        )

        await self.rabbitmq_publisher.publish(
            exchange_name=handler.exchange_name,
            routing_key=handler.routing_key,
            message=TaskMessage(
                id=task_msg.id,
                task_name=handler.next_task_name,
                resource_url=new_resource_url,
                metadata=task_msg.metadata,
            )
            .model_dump_json(exclude_none=True)
            .encode("utf-8"),
        )

        return True

    async def callback(self, msg: AbstractIncomingMessage) -> bool:
        try:
            task_msg = TaskMessage.model_validate_json(msg.body)
        except Exception as e:
            await self.logger.aexception(
                "Error processing message",
                error=str(e),
                body=msg.body.decode("utf-8"),
            )
            return False
        try:
            result = await self._process_message(task_msg)
            if result:
                await self.task_controller.update(
                    TaskUpdate(
                        id=task_msg.id,
                        status=TaskStatus.IN_PROGRESS,
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
            await self.task_controller.update(
                TaskUpdate(
                    id=task_msg.id,
                    status=TaskStatus.FAILED,
                    phase=task_msg.task_name,
                )
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
