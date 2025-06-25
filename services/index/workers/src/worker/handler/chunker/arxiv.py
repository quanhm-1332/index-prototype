from storage import ObjectStorage
from pydantic import AnyUrl
from uuid import uuid4

from ..utils import load_resources, parse_s3_resource_url, get_spacy


def parse_resource_content(resource_content: bytes) -> str:
    return resource_content.decode("utf-8")


def chunk_document(doc: str) -> list[str]:
    nlp = get_spacy()
    processed_doc = nlp(doc)
    chunks = []
    for sent in processed_doc.sents:
        if sent.text.strip():
            chunks.append(sent.text.strip())
    return chunks


async def chunk_arxiv_documents(
    storage: ObjectStorage, resource_url: AnyUrl, separator: str
) -> bytes:
    import json

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

    chunks = []
    for d in docs.split(separator):
        if d.strip():
            chunked_docs = chunk_document(d.strip())
            chunks.extend(chunked_docs)

    return json.dumps(
        {str(uuid4()): chunk for chunk in chunks}, ensure_ascii=False
    ).encode("utf-8")
