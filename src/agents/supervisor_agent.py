from datetime import datetime
from typing import Literal
from ..graph.state import State


def supervisor_node(state: State) -> State:
    # Record step and basic observations
    state["intermediate_steps"] = state.get("intermediate_steps", []) + [
        {
            "agent": "supervisor",
            "ts": datetime.utcnow().isoformat(),
            "observations": {
                "status": state.get("status"),
                "current_agent": state.get("current_agent"),
                "step_index": state.get("step_index"),
            },
        }
    ]

    state["current_agent"] = "supervisor"
    return state


def route_next(state: State) -> Literal["planner", "researcher", "reporter", "FINISH"]:
    # Finish if reporter completed
    if state.get("status") == "finished":
        return "FINISH"

    status = state.get("status")
    if status == "planning":
        return "planner"

    if status == "executing":
        plan = state.get("task_plan", [])
        idx = int(state.get("step_index", 0))
        if 0 <= idx < len(plan):
            # Route to the agent of the current step
            agent = plan[idx].get("agent", "planner")
            # Normalize to known nodes
            if agent in {"researcher", "reporter"}:
                return agent  # type: ignore[return-value]
            return "planner"
        # No more steps; if reporter hasn't run, route to reporter, else finish
        return "reporter"

    # Default safe behavior
    return "planner"
