from typing import TypedDict, List, Dict, Any

class State(TypedDict, total=False):
    request_id: str
    user_query: str
    task_plan: List[Dict[str, Any]]
    context: Dict[str, Any]
    messages: List[Any]
    current_agent: str
    intermediate_steps: List[Dict[str, Any]]
    status: str  # planning | executing | finished | failed
    final_report: str
