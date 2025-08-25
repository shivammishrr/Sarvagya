from datetime import datetime
from ..graph.state import State


def reporter_node(state: State) -> State:
    # Compile a trivial report based on planner plan and context
    plan = state.get("task_plan", [])
    findings = state.get("context", {}).get("research", "")
    report = ["# Report", "", "## Plan:"]
    for step in plan:
        report.append(f"- Step {step.get('step')}: {step.get('agent')} – {step.get('task')}")
    report += ["", "## Findings:", findings or "(none)"]

    state["final_report"] = "\n".join(report)
    state["status"] = "finished"
    state["intermediate_steps"] = state.get("intermediate_steps", []) + [
        {
            "agent": "reporter",
            "ts": datetime.utcnow().isoformat(),
            "output": {"final_report": state["final_report"][:200]},
        }
    ]
    state["current_agent"] = "reporter"
    return state
