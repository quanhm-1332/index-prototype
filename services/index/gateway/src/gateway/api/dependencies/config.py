import yaml
from functools import lru_cache
from tasks import Pipeline


@lru_cache
def load_pipeline() -> Pipeline:
    path = "config/pipeline.yaml"
    with open(
        path,
        "r",
    ) as file:
        config = yaml.safe_load(file)
        return Pipeline.model_validate(config)
