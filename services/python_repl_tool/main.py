from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Python REPL Tool Service", version="0.1.0")


class ExecRequest(BaseModel):
    code: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/exec")
def exec_code(req: ExecRequest) -> dict[str, Any]:
    # Highly simplified and unsafe placeholder. Replace with sandboxed exec later.
    local_ns: dict[str, Any] = {}
    try:
        exec(req.code, {"__builtins__": {}}, local_ns)  # DO NOT USE IN PROD
        return {"ok": True, "locals": {k: str(v) for k, v in local_ns.items()}}
    except Exception as e:
        return {"ok": False, "error": str(e)}
