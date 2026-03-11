from typing import TypedDict, List, Dict, Any, Optional

class FPLState(TypedDict):
    team_id: int
    current_gameweek: int
    error: Optional[str]

    # Manager metadata
    manager_name: str
    team_name: str
    overall_points: int
    overall_rank: int
    bank_balance: float

    # Rich player data
    my_team_players: List[Dict[str, Any]]
    top_targets: List[Dict[str, Any]]

    # Fixture calendar: {team_id: [{gw, opponent, is_home, difficulty}, ...]}
    fixture_calendar: Dict[int, List[Dict[str, Any]]]

    # Manager GW history for chart
    manager_history: List[Dict[str, Any]]

    # Chips used/available
    chips_used: List[Dict[str, Any]]

    # Differential players (low ownership, high form)
    differentials: List[Dict[str, Any]]

    # Pre-computed transfer options for the weakest players
    transfer_options: Dict[str, Any]

    # Math node outputs
    fixture_scores: Dict[int, float]
    form_scores: Dict[int, float]

    # Agent outputs
    captain_picks_report_markdown: str
    transfer_suggestions_report_markdown: str
    final_report_markdown: str
