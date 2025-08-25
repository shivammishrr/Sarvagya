from datetime import datetime
from ..graph.state import State


def planner_node(state: State) -> State:
    # Create a trivial plan for MVP
    plan = [
        {"step": 1, "agent": "researcher", "task": "gather info"},
        {"step": 2, "agent": "reporter", "task": "summarize"},
    ]
    state["task_plan"] = plan
    state["intermediate_steps"] = state.get("intermediate_steps", []) + [
        {
            "agent": "planner",
            "ts": datetime.utcnow().isoformat(),
            "output": {"task_plan": plan},
        }
    ]
    # Move to execution phase; start from first step
    state["status"] = "executing"
    state["step_index"] = 0
    state["current_agent"] = "planner"
    return state
