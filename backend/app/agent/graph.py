from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.nodes.intake import intake_node
from app.agent.nodes.recommendation import recommendation_node
from app.agent.nodes.calculation import calculation_node
from app.agent.nodes.review import review_node
from app.agent.nodes.generation import generation_node


def router(state: AgentState) -> str:
    """Entry router: dispatch to the correct phase node based on current_phase."""
    phase = state.get("current_phase", "intake")
    if phase in ("intake", "recommendation", "calculation", "review", "generation"):
        return phase
    return END


def route_after_intake(state: AgentState) -> str:
    """After intake: advance to recommendation or pause for more user input."""
    if state.get("current_phase") == "recommendation":
        return "recommendation"
    return END  # stay in intake, wait for next message


def route_after_recommendation(state: AgentState) -> str:
    """After recommendation: always pause — user must click Continue to advance."""
    return END


def route_after_calculation(state: AgentState) -> str:
    """After calculation: always pause — user must click Continue to advance."""
    return END


def route_after_review(state: AgentState) -> str:
    """After review: always pause — user must click Continue to advance."""
    return END


def route_after_generation(state: AgentState) -> str:
    return END


def build_graph() -> StateGraph:
    """Build the TVO Proposal Agent LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intake", intake_node)
    workflow.add_node("recommendation", recommendation_node)
    workflow.add_node("calculation", calculation_node)
    workflow.add_node("review", review_node)
    workflow.add_node("generation", generation_node)

    # Entry point: router dispatches to the correct phase
    workflow.set_conditional_entry_point(router)

    # Each node either advances to the next phase or returns to END (waits for user)
    workflow.add_conditional_edges("intake", route_after_intake)
    workflow.add_conditional_edges("recommendation", route_after_recommendation)
    workflow.add_conditional_edges("calculation", route_after_calculation)
    workflow.add_conditional_edges("review", route_after_review)
    workflow.add_conditional_edges("generation", route_after_generation)

    return workflow


def compile_graph():
    """Compile the graph with memory checkpointer."""
    workflow = build_graph()
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# Singleton compiled graph
graph = compile_graph()
