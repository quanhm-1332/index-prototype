from langchain_community.document_loaders import ArxivLoader
from structlog.stdlib import BoundLogger

from logs import get_logger


async def query_arxiv(
    query: str,
    max_results: int = 10,
    logger: BoundLogger = get_logger("crawler.arxiv_loader"),
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

    await logger.ainfo(f"Retrieved {len(results)} papers from Arxiv")
    return results
