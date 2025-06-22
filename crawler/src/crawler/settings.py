from functools import lru_cache
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from pydantic import BaseModel

from broker import RabbitMQSettings


class RabbitMQConnectorSettings(BaseModel):
    exchange_name: str
    routing_key: str
    queue_name: str


class CrawlerSettings(BaseSettings):
    rabbitmq: RabbitMQSettings

    publisher_connector: RabbitMQConnectorSettings
    subscriber_connector: RabbitMQConnectorSettings

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )


@lru_cache
def get_settings() -> CrawlerSettings:
    """
    Get the crawler settings, caching the result for performance.

    Returns:
        CrawlerSettings: The settings instance.
    """
    return CrawlerSettings()  # type: ignore
