from functools import lru_cache
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from pydantic import BaseModel, HttpUrl

from broker import RabbitMQSettings
from db import PostgreSQLSettings
from storage import MinioSettings


class MasterConnectorSettings(BaseModel):
    url: HttpUrl


class Settings(BaseSettings):
    rabbitmq: RabbitMQSettings
    postgre: PostgreSQLSettings
    minio: MinioSettings

    master: MasterConnectorSettings

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
            YamlConfigSettingsSource(
                settings_cls,
                yaml_file="config/worker.yaml",
            ),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
