from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys, os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "FPL_AI_Copilot")

from src.graph import create_fpl_graph

app = FastAPI(title="FPL AI Copilot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    team_id: int

app_graph = create_fpl_graph()

ALL_CHIPS = {"wildcard", "bboost", "3xc", "freehit"}
CHIP_LABELS = {
    "wildcard": "Wildcard",
    "bboost": "Bench Boost",
    "3xc": "Triple Captain",
    "freehit": "Free Hit",
}

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/api/analyze")
def analyze_team(request: AnalyzeRequest):
    initial_state = {"team_id": request.team_id, "error": None}

    try:
        fs = app_graph.invoke(initial_state)
        if fs.get("error"):
            return {"error": fs["error"]}

        all_players = fs.get('my_team_players', [])
        starting_xi = [p for p in all_players if p.get('multiplier', 0) > 0]
        bench = [p for p in all_players if p.get('multiplier', 0) == 0]

        # Chip status
        chips_used = fs.get('chips_used', [])
        used_names = {c['name'] for c in chips_used}
        chips_status = []
        for chip_key in ["wildcard", "bboost", "3xc", "freehit"]:
            chips_status.append({
                "key": chip_key,
                "label": CHIP_LABELS[chip_key],
                "used": chip_key in used_names,
            })

        return {
            "team_id": request.team_id,
            "gameweek": fs.get('current_gameweek'),
            "manager_name": fs.get('manager_name', ''),
            "team_name": fs.get('team_name', ''),
            "overall_points": fs.get('overall_points', 0),
            "overall_rank": fs.get('overall_rank', 0),
            "bank_balance": fs.get('bank_balance', 0),
            "starting_xi": starting_xi,
            "bench": bench,
            "top_targets": fs.get('top_targets', [])[:12],
            "differentials": fs.get('differentials', [])[:10],
            "fixture_calendar": fs.get('fixture_calendar', {}),
            "manager_history": fs.get('manager_history', []),
            "chips_status": chips_status,
            "captain_analysis": fs.get('captain_picks_report_markdown', ''),
            "transfer_analysis": fs.get('transfer_suggestions_report_markdown', ''),
            "error": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
