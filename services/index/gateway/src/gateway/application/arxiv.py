from dataclasses import dataclass
from ..domain.arxiv import ArxivQueryPreprocessor, ArxivTaskCreator
from ..domain.publish import publish_task, create_task

from tasks import TaskController, TaskCreate, TaskStatus
from broker import RabbitMQPublisher, TaskMessage


@dataclass
class ArxivIndexer:
    controller: TaskController
    publisher: RabbitMQPublisher

    async def run(
        self,
        query: str,
        exchange_name: str,
        routing_key: str,
        task_name: str,
        max_results: int | None = None,
    ):
        preprocessor = ArxivQueryPreprocessor()
        task_creator = ArxivTaskCreator(task_name=task_name)

        # Preprocess the query
        processed_query = await preprocessor.preprocess(query, max_results)

        # Create a task message
        task_message = await task_creator.create(processed_query)

        # Publish the task to the broker
        await publish_task(
            publisher=self.publisher,
            task_msg=task_message,
            exchange_name=exchange_name,
            routing_key=routing_key,
        )

        # Optionally, create a task in the database
        await create_task(self.controller, task_message.id, "arxiv", "crawler")

        return task_message.id
