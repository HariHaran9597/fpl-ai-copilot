from ..state import FPLState
from ..fpl_client import FPLClient, FPLAPIError
import logging

logger = logging.getLogger(__name__)

TEAM_COLORS = {
    1: "#EF0107", 2: "#670E36", 3: "#0057B8", 4: "#DA291C",
    5: "#E30613", 6: "#034694", 7: "#1B458F", 8: "#003399",
    9: "#FFFFFF", 10: "#003090", 11: "#C8102E", 12: "#6CABDD",
    13: "#DA291C", 14: "#241F20", 15: "#FBEE23", 16: "#E53233",
    17: "#FF0000", 18: "#132257", 19: "#7A263A", 20: "#FDB913",
}
POSITION_MAP = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
ALL_CHIPS = {"wildcard", "bboost", "3xc", "freehit"}


def _build_player_obj(p, pick, teams_map, fixtures_by_team):
    """Build a rich player dict from raw element + pick data."""
    team_info = teams_map.get(p.get('team', 0), {})
    photo_code = str(p.get('code', ''))
    team_id = p.get('team', 0)

    obj = {
        'id': p['id'],
        'name': p.get('web_name', 'Unknown'),
        'full_name': f"{p.get('first_name', '')} {p.get('second_name', '')}",
        'photo_url': f"https://resources.premierleague.com/premierleague/photos/players/250x250/p{photo_code}.png",
        'team_id': team_id,
        'team_name': team_info.get('name', ''),
        'team_short': team_info.get('short_name', ''),
        'team_color': TEAM_COLORS.get(team_id, '#333'),
        'position': POSITION_MAP.get(p.get('element_type', 0), 'UNK'),
        'now_cost': p.get('now_cost', 0) / 10.0,
        'total_points': p.get('total_points', 0),
        'form': float(p.get('form', 0)),
        'points_per_game': float(p.get('points_per_game', 0)),
        'goals_scored': p.get('goals_scored', 0),
        'assists': p.get('assists', 0),
        'clean_sheets': p.get('clean_sheets', 0),
        'minutes': p.get('minutes', 0),
        'xG': float(p.get('expected_goals', 0)),
        'xA': float(p.get('expected_assists', 0)),
        'ict_index': float(p.get('ict_index', 0)),
        'influence': float(p.get('influence', 0)),
        'creativity': float(p.get('creativity', 0)),
        'threat': float(p.get('threat', 0)),
        'selected_by_percent': float(p.get('selected_by_percent', 0)),
        # Injury / news
        'news': p.get('news', ''),
        'status': p.get('status', 'a'),  # a=available, d=doubtful, i=injured, u=unavailable, s=suspended, n=not available
        'chance_of_playing': p.get('chance_of_playing_next_round'),
        # Price changes
        'cost_change_event': p.get('cost_change_event', 0) / 10.0,
        'transfers_in_event': p.get('transfers_in_event', 0),
        'transfers_out_event': p.get('transfers_out_event', 0),
        # Set-piece info
        'penalties_order': p.get('penalties_order'),
        'corners_order': p.get('corners_and_indirect_freekicks_order'),
        'freekicks_order': p.get('direct_freekicks_order'),
        # Upcoming fixtures for this player's team
        'upcoming_fixtures': fixtures_by_team.get(team_id, [])[:5],
    }

    if pick:
        obj['selling_price'] = pick.get('selling_price', p.get('now_cost', 0)) / 10.0
        obj['is_captain'] = pick.get('is_captain', False)
        obj['is_vice_captain'] = pick.get('is_vice_captain', False)
        obj['multiplier'] = pick.get('multiplier', 1)

    return obj


def fetch_data_node(state: FPLState) -> dict:
    team_id = state.get("team_id")
    client = FPLClient()

    try:
        bootstrap = client.get_bootstrap_static()
        elements = bootstrap.get('elements', [])
        teams_raw = bootstrap.get('teams', [])
        events = bootstrap.get('events', [])
        element_types = {et['id']: et['singular_name_short'] for et in bootstrap.get('element_types', [])}

        teams_map = {t['id']: t for t in teams_raw}
        elements_map = {e['id']: e for e in elements}

        # Current gameweek
        next_event = next((e for e in events if e['is_next']), None)
        current_event = next((e for e in events if e['is_current']), None)
        current_gw = next_event['id'] if next_event else (current_event['id'] if current_event else 1)

        # ── Fixture Calendar ──
        all_fixtures = client.get_fixtures()
        fixtures_by_team = {}  # {team_id: [{gw, opponent, is_home, difficulty}, ...]}
        teams_short = {t['id']: t['short_name'] for t in teams_raw}

        for fx in all_fixtures:
            gw = fx.get('event')
            if gw is None or gw < current_gw or gw > current_gw + 5:
                continue
            # Home team entry
            h_id, a_id = fx['team_h'], fx['team_a']
            fixtures_by_team.setdefault(h_id, []).append({
                'gw': gw,
                'opponent': teams_short.get(a_id, '?'),
                'is_home': True,
                'difficulty': fx.get('team_h_difficulty', 3),
            })
            fixtures_by_team.setdefault(a_id, []).append({
                'gw': gw,
                'opponent': teams_short.get(h_id, '?'),
                'is_home': False,
                'difficulty': fx.get('team_a_difficulty', 3),
            })

        # Sort each team's fixtures by GW
        for tid in fixtures_by_team:
            fixtures_by_team[tid].sort(key=lambda x: x['gw'])

        # ── Manager Info ──
        entry_data = client.get_manager_info(team_id)
        manager_name = f"{entry_data.get('player_first_name', '')} {entry_data.get('player_last_name', '')}"
        team_name = entry_data.get('name', 'Unknown')
        overall_points = entry_data.get('summary_overall_points', 0)
        overall_rank = entry_data.get('summary_overall_rank', 0)
        bank_balance = entry_data.get('last_deadline_bank', 0) / 10.0

        # ── Manager History + Chips ──
        try:
            history_data = client.get_manager_history(team_id)
            manager_history = [
                {
                    'gw': h['event'],
                    'points': h['points'],
                    'total_points': h['total_points'],
                    'rank': h.get('rank', 0),
                    'overall_rank': h.get('overall_rank', 0),
                    'bench_points': h.get('points_on_bench', 0),
                    'transfers': h.get('event_transfers', 0),
                    'transfer_cost': h.get('event_transfers_cost', 0),
                    'value': h.get('value', 0) / 10.0,
                }
                for h in history_data.get('current', [])
            ]
            chips_used = history_data.get('chips', [])
        except Exception:
            manager_history = []
            chips_used = []

        # ── Manager Picks ──
        picks_data = client.get_manager_picks(team_id, current_gw - 1)
        my_picks_raw = picks_data.get('picks', [])

        my_team_players = []
        for pick in my_picks_raw:
            pid = pick['element']
            p = elements_map.get(pid, {})
            obj = _build_player_obj(p, pick, teams_map, fixtures_by_team)
            my_team_players.append(obj)

        # ── Top Targets ──
        sorted_by_form = sorted(elements, key=lambda x: float(x.get('form', 0)), reverse=True)[:20]
        sorted_by_own = sorted(elements, key=lambda x: float(x.get('selected_by_percent', 0)), reverse=True)[:30]
        top_dict = {p['id']: p for p in sorted_by_form + sorted_by_own}
        top_targets = [_build_player_obj(p, None, teams_map, fixtures_by_team) for p in top_dict.values()]

        # ── Differentials: High form, low ownership ──
        differentials = []
        for el in elements:
            form_val = float(el.get('form', 0))
            own_val = float(el.get('selected_by_percent', 0))
            if form_val >= 4.0 and own_val < 5.0 and el.get('total_points', 0) > 40 and el.get('minutes', 0) > 500:
                if el.get('status', 'a') == 'a':
                    differentials.append(_build_player_obj(el, None, teams_map, fixtures_by_team))
        differentials.sort(key=lambda x: x['form'], reverse=True)
        differentials = differentials[:12]

        # ── Pre-compute Mathematical Optimal Transfer ──
        # Fixes the LLM optimization limitation by using a deterministic solver on Expected Points (xP)
        from ..optimization.solver import optimize_transfer_knapsack
        
        my_team_ids = {p['id'] for p in my_team_players}
        available_players = []
        for el in elements:
            if el['id'] not in my_team_ids and el.get('status', 'a') == 'a':
                available_players.append(_build_player_obj(el, None, teams_map, fixtures_by_team))
                
        p_out, p_in, xp_gain = optimize_transfer_knapsack(my_team_players, available_players, bank_balance, fixtures_by_team)
        
        transfer_options = {}
        if p_out and p_in:
            transfer_options[p_out['name']] = {
                'player_out': p_out['name'],
                'player_out_xp': round(p_out.get('xP', 0), 2),
                'player_in': p_in['name'],
                'player_in_xp': round(p_in.get('xP', 0), 2),
                'xp_delta': round(xp_gain, 2),
                'cost': p_in.get('now_cost', 0),
                'budget': round(p_out.get('selling_price', 0) + bank_balance, 2)
            }


        return {
            "current_gameweek": current_gw,
            "manager_name": manager_name,
            "team_name": team_name,
            "overall_points": overall_points,
            "overall_rank": overall_rank,
            "bank_balance": bank_balance,
            "my_team_players": my_team_players,
            "top_targets": top_targets,
            "fixture_calendar": fixtures_by_team,
            "manager_history": manager_history,
            "chips_used": chips_used,
            "differentials": differentials,
            "transfer_options": transfer_options,
            "error": None,
        }

    except FPLAPIError as e:
        logger.error(f"FPL API crashing: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in DataNode: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
