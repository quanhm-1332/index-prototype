from pydantic import AnyUrl
from storage import ObjectStorage
import spacy
from dataclasses import dataclass, asdict

from ..utils import load_resources, parse_s3_resource_url, get_spacy


@dataclass(slots=True)
class Entity:
    name: str
    type: str
    description: str


def parse_resource_content(resource_content: bytes) -> dict[str, str]:
    import json

    try:
        resource_json = json.loads(resource_content.decode("utf-8"))
        return resource_json
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


def extract_from_sent(sent: str) -> list[Entity]:
    nlp = get_spacy()
    doc = nlp(sent)
    entities = []
    for ent in doc.ents:
        description = spacy.explain(ent.label_)  # type: ignore
        entities.append(
            Entity(
                name=ent.text,
                type=ent.label_,
                description=description if description else "",
            )
        )
    return entities


def extract_entities_from_docs(docs: dict[str, str]) -> list[dict[str, str]]:
    extracted_entities = []
    for k, v in docs.items():
        if v.strip():
            entities = extract_from_sent(v.strip())
            if entities:
                for entity in entities:

                    extracted_entities.append({"chunk_id": k, **asdict(entity)})
    return extracted_entities


async def extract_entities(
    resource_url: AnyUrl,
    storage: ObjectStorage,
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

    extracted_output = {
        "chunks": [{"id": k, "text": v} for k, v in docs.items()],
        "entities": extract_entities_from_docs(docs),
    }
    return json.dumps(extracted_output, ensure_ascii=False).encode("utf-8")
