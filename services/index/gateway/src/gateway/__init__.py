from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from broker import RabbitMQPool
from db import PostgresClient

from .api.routers import arxiv_router
from .api.routers import tasks_router
from .api.routers import pipeline_router
from .api.models import Resources
from .api.dependencies.config import load_pipeline

from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.resources = Resources(
        broker=RabbitMQPool(settings.rabbitmq),
        db=await PostgresClient.init(settings.postgre),
    )
    pipeline = load_pipeline()
    await app.state.resources.broker.bind(
        exchange_name="gateway",
        queue_name=pipeline.backlog_queue_name,
        routing_key="gateway.#",
    )
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],  # Adjust this to your needs
    allow_headers=["*"],  # Adjust this to your needs
)

app.include_router(arxiv_router)
app.include_router(tasks_router)
app.include_router(pipeline_router)


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=19000)
