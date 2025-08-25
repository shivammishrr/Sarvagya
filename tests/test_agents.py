from src.graph.state import State
from src.agents.planner_agent import planner_node
from src.agents.researcher_agent import researcher_node
from src.agents.reporter_agent import reporter_node
from src.agents.supervisor_agent import route_next


def _base_state() -> State:
    return {
        "request_id": "t",
        "user_query": "test",
        "task_plan": [],
        "context": {},
        "messages": [],
        "current_agent": "",
        "intermediate_steps": [],
        "status": "planning",
        "final_report": "",
    }


def test_planner_creates_plan_and_moves_to_execution():
    s = _base_state()
    s2 = planner_node(s)
    assert s2["status"] == "executing"
    assert s2.get("task_plan")
    assert s2.get("step_index") == 0


def test_researcher_writes_findings_and_advances_index():
    s = _base_state()
    s = planner_node(s)
    s2 = researcher_node(s)
    assert "research" in s2.get("context", {})
    assert s2.get("step_index", 0) == 1


def test_reporter_finishes_with_report():
    s = _base_state()
    s = planner_node(s)
    s = researcher_node(s)
    s2 = reporter_node(s)
    assert s2["status"] == "finished"
    assert isinstance(s2.get("final_report"), str) and s2["final_report"]


def test_route_next_flow():
    s = _base_state()
    assert route_next(s) == "planner"
    s = planner_node(s)
    # Should route to researcher first
    assert route_next(s) == "researcher"
