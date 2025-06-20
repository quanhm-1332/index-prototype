from pydantic import BaseModel, SecretStr


class MinioSettings(BaseModel):
    endpoint: str
    access_key: SecretStr
    secret_key: SecretStr
