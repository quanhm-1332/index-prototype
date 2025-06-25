import json

from pydantic import AnyUrl
from langchain_community.document_loaders import ArxivLoader
from structlog.stdlib import BoundLogger

from logs import get_logger


async def query_arxiv(
    query: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Query Arxiv for papers matching the given query string.

    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
        logger (BoundLogger): Logger instance for logging.

    Returns:
        list[dict]: List of dictionaries containing paper metadata.
    """
    loader = ArxivLoader(
        query=query,
        load_max_docs=max_results,
    )
    documents = loader.alazy_load()

    results = []
    async for doc in documents:
        results.append(
            {
                "content": doc.page_content,
                "title": doc.metadata.get("title"),
                "authors": doc.metadata.get("authors"),
                "summary": doc.metadata.get("summary"),
                "published": doc.metadata.get("published"),
                "url": doc.metadata.get("url"),
            }
        )

    return results


async def handle_arxiv_query(
    resource_url: AnyUrl,
):
    """
    Handle the arXiv query and publish results.
    """
    query = resource_url.query
    if query is None:
        raise ValueError("Query parameter is required for arxiv resource")
    queries = query.split("&")
    if len(queries) != 2:
        raise ValueError(
            "Invalid query format. Expected 'query=<value>&limit=<value>'."
        )
    query = queries[0].split("=")[1]
    max_results = queries[1].split("=")[1]

    _max_results = 1
    if not max_results.isdigit():
        _max_results = 1

    if int(max_results) <= 0:
        _max_results = 1

    docs = await query_arxiv(
        query,
        max_results=int(_max_results),
    )

    _docs_object = {"docs": docs}

    _docs_json = json.dumps(_docs_object, ensure_ascii=False)
    _docs_bytes = _docs_json.encode("utf-8")

    return _docs_bytes
