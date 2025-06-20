from pydantic import BaseModel, SecretStr


class PostgresSettings(BaseModel):
    host: str
    port: int
    username: str
    password: SecretStr
