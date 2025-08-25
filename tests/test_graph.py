from src.graph.workflow import build_graph
from src.graph.state import State


def test_graph_builds():
    graph = build_graph()
    assert graph is not None


def test_graph_streams_basic():
    graph = build_graph()
    initial_state: State = {
        "request_id": "test-1",
        "user_query": "test",
        "task_plan": [],
        "context": {},
        "messages": [],
        "current_agent": "planner",
        "intermediate_steps": [],
        "status": "planning",
        "final_report": "",
    }
    # Stream and ensure we receive at least one update
    updates = list(graph.stream(initial_state))
    assert len(updates) > 0
