from dataclasses import dataclass
from broker import TaskMessage
import uuid


@dataclass
class ArxivQueryPreprocessor:
    async def preprocess(self, query: str, max_results: int | None = None) -> str:
        return f"web://arxiv?query={query.strip()}&limit={max_results if max_results else 1}"


@dataclass
class ArxivTaskCreator:
    task_name: str

    async def create(self, query: str) -> TaskMessage:
        # Here you can implement any postprocessing logic if needed
        return TaskMessage(
            id=uuid.uuid4().hex,
            resource_url=query,
            task_name=self.task_name,
            metadata={},
        )
