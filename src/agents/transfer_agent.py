import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import FPLState

logger = logging.getLogger(__name__)

def recommend_transfers_node(state: FPLState) -> dict:
    """
    Hybrid Mathematical/GenAI Transfer Solver.
    Takes the mathematically proven optimal Knapsack transfer from the Py solver 
    and uses the LLM solely as an 'Explainer Layer'.
    """
    if state.get("error"):
        return {}

    transfer_options = state.get("transfer_options", {})
    if not transfer_options:
        return {"transfer_suggestions_report_markdown": "> Mathematics indicate your current squad is optimally configured for the next 5 gameweeks based on Expected Points (xP). Save your transfer."}

    # Extract the pre-computed mathematical optimum
    opt = list(transfer_options.values())[0]

    context = f"""
    The mathematical 'Knapsack Solver' has proven the optimal transfer to maximize Expected Points (xP):
    
    OUT: {opt['player_out']} (Current Projected xP over 5 GWs: {opt.get('player_out_xp', 0)})
    IN: {opt['player_in']} (New Projected xP over 5 GWs: {opt.get('player_in_xp', 0)})
    
    Net xP Gain: +{opt.get('xp_delta', 0)}
    Price of Incoming Player: £{opt.get('cost', 0)}m
    Total Available Budget: £{opt.get('budget', 0)}m
    """

    system_prompt = (
        "You are the Explanatory Layer of a highly advanced FPL Artificial Intelligence.\n"
        "Your optimization engine has mathematically proven the best single transfer (OUT and IN) "
        "based on Expected Points (xP), Form constraints, and Fixture Difficulty (FDR).\n"
        "Explain to the human manager WHY this mathematically optimal transfer makes strategic sense.\n"
        "Be concise (max 3 bullets). Mention the mathematical gain and budget feasibility.\n"
        "Do not invent facts, simply explain the mathematical truth."
    )

    try:
        llm = ChatGroq(model="moonshotai/kimi-k2-instruct-0905", temperature=0.1)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        return {"transfer_suggestions_report_markdown": response.content}
    except Exception as e:
        logger.error(f"Error in Transfer Agent: {e}")
        return {"transfer_suggestions_report_markdown": f"> Mathematical optimization complete, but LLM explanation failed: {e}"}
