import pytest

from crawler.loader import query_arxiv


@pytest.mark.asyncio
async def test_query_arxiv():
    query = "quantum computing"
    max_results = 5

    results = await query_arxiv(query, max_results)

    assert isinstance(results, list)
    assert len(results) <= max_results

    for paper in results:
        assert "content" in paper
        assert "title" in paper
        assert "authors" in paper
        assert "summary" in paper
        assert "published" in paper
        assert "url" in paper

    # Check if the content is not empty
    for paper in results:
        assert paper["content"] != ""
        assert paper["title"] != ""
        assert paper["authors"] != ""
        assert paper["summary"] != ""
        assert paper["published"] != ""
        assert paper["url"] != ""
