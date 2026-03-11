from ..state import FPLState


def calculate_fixture_scores(state: FPLState) -> dict:
    """Compute a fixture appeal score per player based on real upcoming FDR."""
    if state.get("error"):
        return {}

    fixture_cal = state.get("fixture_calendar", {})
    all_players = state.get("my_team_players", []) + state.get("top_targets", [])

    fixture_scores = {}
    for p in all_players:
        pid = p['id']
        team_id = p.get('team_id', 0)
        team_fixtures = fixture_cal.get(team_id, [])
        if team_fixtures:
            # Average difficulty of next 3 fixtures, invert so lower difficulty = higher score
            difficulties = [f['difficulty'] for f in team_fixtures[:3]]
            avg_diff = sum(difficulties) / len(difficulties)
            # Score out of 10: difficulty 1 = score 10, difficulty 5 = score 2
            score = round(max(1, 12 - (avg_diff * 2)), 1)
        else:
            score = 5.0
        fixture_scores[pid] = score

    return {"fixture_scores": fixture_scores}


def calculate_form_scores(state: FPLState) -> dict:
    if state.get("error"):
        return {}

    form_scores = {}
    for p in state.get("my_team_players", []) + state.get("top_targets", []):
        form_scores[p['id']] = p.get('form', 0)

    return {"form_scores": form_scores}
