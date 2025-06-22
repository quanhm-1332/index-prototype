from pydantic import BaseModel, SecretStr


class RabbitMQSettings(BaseModel):
    """RabbitMQ settings for the broker."""

    scheme: str = "amqp"
    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: SecretStr

    max_conn: int = 2
    max_channel: int = 10
