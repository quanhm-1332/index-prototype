from typing import Annotated
from fastapi import Depends, Request
from functools import lru_cache

from db import PostgresClient
from broker import RabbitMQPool, RabbitMQPublisher, RabbitMQSubscriber
from tasks import TaskController, PostgreSQLController, Pipeline
from ..dependencies.config import load_pipeline

from ..models import Resources


async def get_resources(request: Request) -> Resources:
    """
    Dependency to provide access to shared resources like database and message broker.
    This function retrieves the resources from the request state.
    """
    if not hasattr(request.app.state, "resources"):
        raise ValueError("Resources are not initialized in the request state.")
    resources = request.app.state.resources
    if not isinstance(resources, Resources):
        raise ValueError("Resources are not properly initialized in the request state.")
    return resources


async def get_db_client(
    resources: Annotated[Resources, Depends(get_resources)],
) -> PostgresClient:
    """
    Dependency to provide access to the Postgres database client.
    This function retrieves the database client from the resources.
    """
    return resources.db


async def get_task_controller(
    db_client: Annotated[PostgresClient, Depends(get_db_client)],
) -> TaskController:
    return PostgreSQLController(db_client)


async def get_broker(
    resources: Annotated[Resources, Depends(get_resources)],
    pipeline: Annotated[Pipeline, Depends(load_pipeline)],
) -> RabbitMQPool:
    """
    Dependency to provide access to the RabbitMQ message broker.
    This function retrieves the message broker from the resources.
    """
    pool = resources.broker
    return pool


async def get_publisher(
    rabbitmq_pool: Annotated[RabbitMQPool, Depends(get_broker)],
) -> RabbitMQPublisher:
    """
    Dependency to provide access to the RabbitMQ publisher.
    This function retrieves the publisher from the resources.
    """
    return RabbitMQPublisher(rabbitmq_pool)
