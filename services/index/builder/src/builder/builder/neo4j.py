from dataclasses import dataclass
from neo4j import AsyncDriver, AsyncManagedTransaction

from storage import ObjectStorage
from pydantic import AnyUrl

from ._interface import IBuilder, ResourceInvalid


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


@dataclass(slots=True)
class Entity:
    name: str
    type: str
    description: str


@dataclass
class Neo4jBuilder(IBuilder):
    driver: AsyncDriver

    async def build(self, resources_url: str) -> None:
        try:
            _url = AnyUrl(resources_url)
        except Exception as e:
            raise ResourceInvalid(resources_url, "Invalid resource format") from e

        match (_url.scheme, _url.host):
            case ("minio", "arxiv"):
                try:
                    resource_content = await self._build_graph(
                        resource_url=_url,
                    )
                except ValueError as e:
                    raise ResourceInvalid(resources_url, str(e))
                return resource_content
            case _:
                raise ResourceInvalid(
                    resources_url,
                    f"Unsupported resource scheme and host: {_url.scheme}, {_url.host}",
                )

    async def _build_graph(self, resource_url: AnyUrl):
        bucket_name, object_name = parse_s3_resource_url(resource_url)
        resource_content = await load_resources(
            storage=self.storage,
            bucket_name=bucket_name,
            object_name=object_name,
        )

        if resource_content is None:
            raise ValueError(f"Resource not found: {resource_url}")

        data = self._parse_resource_content(resource_content)
        chunks: list[dict[str, str]] = data.get("chunks", [])
        entities: list[dict[str, str]] = data.get("entities", [])

        await self._run_transaction(self._create_index)
        await self._run_transaction(self._create_chunks, chunks)
        await self._run_transaction(self._create_entities, entities)
        await self._run_transaction(self._create_relationships, entities)

    async def _run_transaction(self, tx_func, *args, **kwargs):
        async with self.driver.session() as session:
            await session.execute_write(tx_func, *args, **kwargs)

    async def _create_index(self, tx: AsyncManagedTransaction):

        await tx.run("CREATE INDEX IF NOT EXISTS FOR (c:Chunk) ON (c.id)")
        await tx.run("CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.name)")
        await self.logger.ainfo("Created indexes in Neo4j")

    async def _create_chunks(
        self, tx: AsyncManagedTransaction, chunks: list[dict[str, str]]
    ):
        query = """
        UNWIND $chunks AS chunk
        MERGE (c:Chunk {id: chunk.id, text: chunk.text})
        RETURN COUNT(c) AS no_chunks
        """

        result = await tx.run(query, chunks=chunks)
        no_chunks = await result.single()
        if not no_chunks:
            raise ValueError("No chunks were created in the database.")
        if no_chunks["no_chunks"] != len(chunks):
            raise ValueError(
                f"Expected {len(chunks)} chunks, but got {no_chunks['no_chunks']}."
            )
        await self.logger.ainfo(
            "Created chunks in Neo4j",
            no_chunks=no_chunks["no_chunks"],
        )

    async def _create_entities(
        self, tx: AsyncManagedTransaction, entities: list[dict[str, str]]
    ):
        query = """
        UNWIND $entities AS entity
        MERGE (e:Entity {name: entity.name, type: entity.type, description: entity.description})
        RETURN COUNT(e) AS no_entities
        """

        result = await tx.run(query, entities=entities)
        no_entities = await result.single()
        if not no_entities:
            raise ValueError("No entities were created in the database.")
        if no_entities["no_entities"] != len(entities):
            raise ValueError(
                f"Expected {len(entities)} entities, but got {no_entities['no_entities']}."
            )
        await self.logger.ainfo(
            "Created entities in Neo4j",
            no_entities=no_entities["no_entities"],
        )

    async def _create_relationships(
        self, tx: AsyncManagedTransaction, entities: list[dict[str, str]]
    ):
        query = """
        UNWIND $entities AS entity
        MATCH (c:Chunk {id: entity.chunk_id}), (e:Entity {name: entity.name})
        MERGE (c)-[:CONTAINS]->(e)
        RETURN COUNT(*) AS no_relationships
        """

        result = await tx.run(query, entities=entities)
        no_relationships = await result.single()
        if not no_relationships:
            raise ValueError("No relationships were created in the database.")
        await self.logger.ainfo(
            "Created relationships in Neo4j",
            no_relationships=no_relationships["no_relationships"],
        )

    def _parse_resource_content(
        self, resource_content: bytes
    ) -> dict[str, list[dict[str, str]]]:
        import json

        try:
            resource_json = json.loads(resource_content.decode("utf-8"))
            return resource_json
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e
