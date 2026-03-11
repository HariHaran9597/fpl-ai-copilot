from langgraph.graph import StateGraph, START, END
from typing import Dict, Any

from .state import FPLState
from .nodes.data_node import fetch_data_node
from .nodes.math_nodes import calculate_fixture_scores, calculate_form_scores
from .agents.captain_agent import select_captain_node
from .agents.transfer_agent import recommend_transfers_node
from .agents.report_agent import generate_report_node

def route_after_data(state: FPLState):
    """Router to skip AI reasoning if API is down."""
    if state.get("error"):
        return "report"
    return "fixture_calc"

def create_fpl_graph() -> StateGraph:
    workflow = StateGraph(FPLState)
    
    workflow.add_node("data", fetch_data_node)
    
    workflow.add_node("fixture_calc", calculate_fixture_scores)
    workflow.add_node("form_calc", calculate_form_scores)
    
    workflow.add_node("captain", select_captain_node)
    workflow.add_node("transfer", recommend_transfers_node)
    workflow.add_node("report", generate_report_node)

    # Sequence
    workflow.add_edge(START, "data")
    workflow.add_conditional_edges("data", route_after_data, {
        "fixture_calc": "fixture_calc", 
        "report": "report"
    })
    
    workflow.add_edge("fixture_calc", "form_calc")
    
    # After math, run agents sequentially to avoid LangGraph parallel edge errors
    workflow.add_edge("form_calc", "captain")
    workflow.add_edge("captain", "transfer")
    workflow.add_edge("transfer", "report")
    workflow.add_edge("report", END)

    return workflow.compile()
