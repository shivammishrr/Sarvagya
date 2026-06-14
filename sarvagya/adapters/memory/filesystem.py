import os
from pathlib import Path

from sarvagya.core.types import MemoryEntry


class FileMemory:
    def __init__(self, base_path: str):
        self._base = Path(base_path).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def init_dir(self, path: str) -> None:
        p = self._base / path
        p.mkdir(parents=True, exist_ok=True)
        index_file = p / "MEMORY.md"
        if not index_file.exists():
            index_file.write_text("# Memory Index\n\n", encoding="utf-8")

    def save(
        self, key: str, content: str, metadata: dict | None = None
    ) -> None:
        meta = metadata or {}
        parts = ["---"]
        for k, v in meta.items():
            parts.append(f"{k}: {v}")
        parts.append("---")
        parts.append("")
        parts.append(content)

        file_path = self._base / f"{key}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("\n".join(parts), encoding="utf-8")

        index_file = self._base / "MEMORY.md"
        if index_file.exists():
            with index_file.open("a") as f:
                f.write(f"- [{key}]({key}.md)\n")

    def load(self, key: str) -> MemoryEntry | None:
        file_path = self._base / f"{key}.md"
        if not file_path.exists():
            return None
        content = file_path.read_text(encoding="utf-8")
        metadata: dict = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip()
                body = parts[2].strip()
        return MemoryEntry(key=key, content=body, metadata=metadata)

    def list(self, prefix: str = "") -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for f in self._base.glob(f"{prefix}*.md"):
            if f.name == "MEMORY.md":
                continue
            entry = self.load(f.stem)
            if entry:
                entries.append(entry)
        return entries
