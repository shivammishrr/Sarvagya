from datetime import datetime
from typing import Literal
from ..graph.state import State


def supervisor_node(state: State) -> State:
    # Record step
    state["intermediate_steps"] = state.get("intermediate_steps", []) + [
        {
            "agent": "supervisor",
            "ts": datetime.utcnow().isoformat(),
            "observations": {
                "status": state.get("status"),
                "current_agent": state.get("current_agent"),
            },
        }
    ]

    # Decide: if we just planned, go to FINISH for MVP
    state["current_agent"] = "supervisor"
    if state.get("status") == "planning":
        state["status"] = "finished"
        state["final_report"] = state.get("final_report", "") or "Plan created."
    return state


def route_next(state: State) -> Literal["planner", "FINISH"]:
    if state.get("status") == "finished":
        return "FINISH"
    return "planner"
