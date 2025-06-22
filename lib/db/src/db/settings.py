from pydantic import BaseModel, SecretStr


class PostgreSQLSettings(BaseModel):
    host: str
    port: int
    username: str
    password: SecretStr
