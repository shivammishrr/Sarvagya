from typing import Protocol

from sarvagya.core.types import MemoryEntry


class Memory(Protocol):
    def save(
        self, key: str, content: str, metadata: dict | None = None
    ) -> None:
        ...

    def load(self, key: str) -> MemoryEntry | None:
        ...

    def list(self, prefix: str = "") -> list[MemoryEntry]:
        ...

    def init_dir(self, path: str) -> None:
        ...
