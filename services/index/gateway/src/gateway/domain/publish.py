from tasks import TaskController, TaskCreate, TaskStatus
from broker import RabbitMQPublisher, TaskMessage


async def create_task(
    controller: TaskController, task_id: str, department: str, phase: str
):
    task = TaskCreate(
        id=task_id,
        status=TaskStatus.PENDING,
        department=department,
        phase=phase,
    )
    return await controller.create(task)


async def publish_task(
    publisher: RabbitMQPublisher,
    task_msg: TaskMessage,
    exchange_name: str,
    routing_key: str,
):
    await publisher.publish(
        exchange_name=exchange_name,
        routing_key=routing_key,
        message=task_msg.model_dump_json().encode("utf-8"),
    )
