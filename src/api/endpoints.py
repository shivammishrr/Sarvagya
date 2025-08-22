from typing import AsyncGenerator
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from ..graph.workflow import build_graph
from ..graph.state import State
from .schemas import ChatRequest

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(body: ChatRequest) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[dict, None]:
        graph = build_graph()
        initial_state: State = {
            "request_id": "req-0001",
            "user_query": body.user_query,
            "task_plan": [],
            "context": {},
            "messages": [],
            "current_agent": "planner",
            "intermediate_steps": [],
            "status": "planning",
            "final_report": "",
        }
        for update in graph.stream(initial_state):
            yield {"event": "update", "data": str(update)}
        yield {"event": "complete", "data": "done"}

    return EventSourceResponse(event_generator())
