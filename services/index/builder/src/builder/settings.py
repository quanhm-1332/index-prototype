from functools import lru_cache
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from pydantic import BaseModel, AnyUrl, HttpUrl

from broker import RabbitMQSettings
from db import PostgreSQLSettings
from storage import MinioSettings


class Neo4jDsn(AnyUrl):
    allowed_schemes = {"neo4j", "neo4j+s", "bolt", "bolt+s"}
    user_required = True
    password_required = True
    host_required = True
    port_required = True

    def encoded_string(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    def get_auth(self) -> tuple[str, str]:
        return self.username or "", self.password or ""


class Neo4jSettings(BaseModel):
    dsn: Neo4jDsn


class MasterConnectorSettings(BaseModel):
    url: HttpUrl


class Settings(BaseSettings):
    rabbitmq: RabbitMQSettings
    postgre: PostgreSQLSettings
    minio: MinioSettings
    neo4j: Neo4jSettings
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
                yaml_file="config/builder.yaml",
            ),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
