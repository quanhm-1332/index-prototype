from broker import run
from .pubsub import pubsub
from .settings import get_settings


def main():
    import asyncio

    asyncio.run(pubsub(get_settings()))
