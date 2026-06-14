from typing import Protocol

from sarvagya.core.types import SandboxResult


class Sandbox(Protocol):
    def execute(
        self,
        command: str,
        timeout: int = 120000,
        workdir: str | None = None,
    ) -> SandboxResult:
        ...

    def write_file(self, path: str, content: str) -> None:
        ...

    def read_file(self, path: str) -> str:
        ...
