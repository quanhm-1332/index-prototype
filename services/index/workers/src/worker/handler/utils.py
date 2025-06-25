from functools import lru_cache

from storage import ObjectStorage
from pydantic import AnyUrl


@lru_cache
def get_spacy():
    import spacy

    nlp = spacy.load("en_core_web_sm", exclude=["parser"])
    nlp.enable_pipe("senter")
    return nlp


async def load_resources(
    storage: ObjectStorage, bucket_name: str, object_name: str
) -> bytes | None:
    resource_content = await storage.get_file(bucket_name, object_name)
    return resource_content


def parse_s3_resource_url(resource_url: AnyUrl) -> tuple[str, str]:
    if resource_url.path is None:
        raise ValueError("Resource URL path is required.")
    path = resource_url.path
    paths = path.strip("/").split("/")
    if len(paths) != 2:
        raise ValueError("Invalid resource URL format. Expected 'web/arxiv'.")

    return paths[0], paths[1]


def build_resource_url(
    scheme: str, host: str, bucket_name: str, object_name: str, task_id: str
) -> str:
    return f"{scheme}://{host}/{bucket_name}/{task_id}_{object_name}"
