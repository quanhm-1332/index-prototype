from dataclasses import dataclass


@dataclass
class ArxivQueryPreprocessor:
    async def preprocess(self, query: str, max_results: int | None = None) -> str:
        return f"arxiv://{query.strip()}?{max_results if max_results else 1}"
