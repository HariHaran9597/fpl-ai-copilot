import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from duckduckgo_search import DDGS
from ..state import FPLState

logger = logging.getLogger(__name__)

def get_player_news_rag(player_name: str, team_name: str) -> str:
    """
    Lightweight RAG retrieval simulating unstructured real-world context gathering (News, Pressers).
    Uses DuckDuckGo to find the latest news headlines about a player.
    """
    query = f"{player_name} {team_name} injury news fantasy premier league return"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=2))
            if not results:
                return "No recent critical news."
            return " | ".join([r['title'] for r in results])
    except Exception as e:
        logger.warning(f"RAG Retrieval failed for {player_name}: {e}")
        return "News retrieval unavailable."

def select_captain_node(state: FPLState) -> dict:
    if state.get("error"):
        return {}

    my_team = state.get("my_team_players", [])
    fixture_scores = state.get("fixture_scores", {})

    starters = [p for p in my_team if p.get('multiplier', 0) > 0]
    
    # Identify Top 3 Captaincy Candidates mathematically
    # We prioritize Form + Fixtures
    candidates = []
    for p in starters:
        fdr = fixture_scores.get(p['id'], 5)
        score = p['form'] * 0.6 + fdr * 0.4
        candidates.append((p, score, fdr))
        
    candidates.sort(key=lambda x: x[1], reverse=True)
    top_3 = candidates[:3]

    team_data = "🔍 MATHEMATICAL CAPTAIN CANDIDATES & RAG CONTEXT:\n\n"
    for p, score, fdr in top_3:
        # Perform Live RAG Retrieval for the top 3 candidates only (to save time)
        live_news_context = get_player_news_rag(p['name'], p['team_name'])
        
        team_data += (
            f"🎯 Candidate: **{p['name']}** ({p['position']})\n"
            f"   • Form: {p['form']} | Fixture Appeal (higher=easier): {fdr}/10\n"
            f"   • Set-Pieces: Pens {'Yes' if p.get('penalties_order') == 1 else 'No'}\n"
            f"   • Live RAG News Snippet: {live_news_context}\n\n"
        )

    system_prompt = (
        "You are an elite FPL Captain Advisor equipped with mathematically optimized candidates "
        "and real-time RAG (Retrieval-Augmented Generation) news context.\n\n"
        "Recommend 1 primary captain and 1 vice-captain from the candidates provided.\n"
        "CRITICAL: If the Live RAG News Snippet indicates an injury, rotation risk, or doubt, "
        "you MUST NOT recommend them as primary captain, overriding the math.\n"
        "Explain your reasoning concisely combining the stats + the real-world news.\n"
        "Be concise — max 100 words. Use bullet points."
    )

    try:
        llm = ChatGroq(model="moonshotai/kimi-k2-instruct-0905", temperature=0.1)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze and pick captains:\n\n{team_data}")
        ])
        return {"captain_picks_report_markdown": response.content}
    except Exception as e:
        logger.error(f"Error in Captain Agent: {e}")
        return {"captain_picks_report_markdown": f"> RAG + LLM Error: {e}"}
