from pathlib import Path
from typing import Dict

BASE = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, variables: Dict[str, str] | None = None) -> str:
    path = BASE / f"{name}.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if variables:
        for k, v in variables.items():
            text = text.replace(f"{{{{{k}}}}}", str(v))
    return text
