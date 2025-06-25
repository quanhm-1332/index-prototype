from storage import ObjectStorage
from pydantic import AnyUrl

from ..utils import load_resources, parse_s3_resource_url


def format_arxiv_document(doc: dict) -> str:

    headers = ("content", "title", "authors", "summary", "published", "url")

    doc_str = ""
    for header in headers:

        content = doc.get(header, "")
        if content != "":
            if isinstance(content, list):
                content = ", ".join(content)
            elif isinstance(content, dict):
                content = str(content)
            doc_str += f"{header.capitalize()}: {content}\n"

    return doc_str.strip()


def parse_resource_content(resource_content: bytes) -> list[dict]:
    import json

    try:
        resource_json = json.loads(resource_content.decode("utf-8"))
        return resource_json.get("docs", [])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


async def parse_arxiv_documents(
    storage: ObjectStorage, resource_url: AnyUrl, separator: str
) -> bytes:
    bucket_name, object_name = parse_s3_resource_url(resource_url)
    resource_content = await load_resources(
        storage=storage,
        bucket_name=bucket_name,
        object_name=object_name,
    )

    if resource_content is None:
        raise ValueError(f"Resource not found: {resource_url}")

    docs = parse_resource_content(resource_content)
    if not docs:
        raise ValueError(f"No documents found in resource: {resource_url}")

    formatted_docs = [format_arxiv_document(doc) for doc in docs]
    return separator.join(formatted_docs).encode("utf-8")
