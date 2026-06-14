from typing import Protocol


class WebSearch(Protocol):
    def search(self, query: str, max_results: int = 5) -> str:
        ...
