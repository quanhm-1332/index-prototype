from pydantic import BaseModel, ConfigDict


class ArbitraryBaseModel(BaseModel):
    """
    Custom base model that allows arbitrary types.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
