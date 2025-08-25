from datetime import datetime
from ..graph.state import State
from ..tools.browser_client import BrowserClient


def researcher_node(state: State) -> State:
    # Try to use browser tool if the query looks like a URL, otherwise simulate
    uq = state.get('user_query', '')
    findings: str
    if isinstance(uq, str) and uq.startswith(("http://", "https://")):
        try:
            with BrowserClient() as bc:
                resp = bc.browse(uq)
            title = resp.get("title") or "(no title)"
            content = resp.get("content") or ""
            findings = f"Title: {title}\n\n{content}"
        except Exception as e:
            findings = f"(browser_tool error: {e})\n\nFindings for: {uq}"
    else:
        # Simulated fallback
        findings = f"Findings for: {uq}"
    context = state.get("context", {})
    context["research"] = findings
    state["context"] = context

    # Log step
    state["intermediate_steps"] = state.get("intermediate_steps", []) + [
        {
            "agent": "researcher",
            "ts": datetime.utcnow().isoformat(),
            "output": {"research": findings[:200]},
        }
    ]

    # Advance plan index
    state["step_index"] = int(state.get("step_index", 0)) + 1
    state["current_agent"] = "researcher"
    return state
