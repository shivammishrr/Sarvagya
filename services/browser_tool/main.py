from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI(title="Browser Tool Service", version="0.1.0")


class BrowseRequest(BaseModel):
    url: HttpUrl
    max_chars: int | None = 2000


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/browse")
def browse(req: BrowseRequest):
    # Placeholder: in future, integrate browser-use + readability extraction
    return {
        "url": str(req.url),
        "title": "(stub)",
        "content": "This is a stubbed browser tool response.",
        "truncated": True,
    }
