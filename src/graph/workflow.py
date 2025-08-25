from langgraph.graph import StateGraph, END
from .state import State
from ..agents.supervisor_agent import supervisor_node, route_next
from ..agents.planner_agent import planner_node
from ..agents.researcher_agent import researcher_node
from ..agents.reporter_agent import reporter_node


def build_graph() -> StateGraph:
    graph = StateGraph(State)

    # Nodes
    graph.add_node("planner", planner_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("reporter", reporter_node)

    # Entry
    graph.set_entry_point("planner")

    # Edges via router
    graph.add_edge("planner", "supervisor")
    graph.add_edge("researcher", "supervisor")
    graph.add_edge("reporter", "supervisor")

    def router(state: State):
        nxt = route_next(state)
        return END if nxt == "FINISH" else nxt

    graph.add_conditional_edges(
        "supervisor",
        router,
        {
            "planner": "planner",
            "researcher": "researcher",
            "reporter": "reporter",
        },
    )

    return graph.compile()
