from dataclasses import dataclass


@dataclass
class ArxivIndexer:
    async def run(self, query: str, max_results: int | None = None):
        pass
