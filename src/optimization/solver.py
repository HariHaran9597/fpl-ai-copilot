import pulp
from typing import List, Dict, Any, Tuple, Optional

def calculate_expected_points(player: dict, fixtures_by_team: dict) -> float:
    """
    Mock Expected Points (xP) ML Model.
    In a real app, this would be an XGBoost model. For now, it's a determinist formula
    combining Form, ICT Index, and upcoming Fixture Difficulty (FDR).
    """
    form = float(player.get('form', 0))
    ict = float(player.get('ict_index', 0)) / 10.0  # Normalized
    
    # Calculate FDR impact
    team_id = player.get('team', player.get('team_id', 0))
    team_fixtures = fixtures_by_team.get(team_id, [])
    if team_fixtures:
        difficulties = [f['difficulty'] for f in team_fixtures[:3]]
        avg_diff = sum(difficulties) / len(difficulties)
        fdr_multiplier = max(0.5, (10 - avg_diff) / 5.0) # Difficulty 2 -> Multiplier 1.6
    else:
        fdr_multiplier = 1.0

    xp = (form * 0.5 + ict * 0.5) * fdr_multiplier
    return round(xp, 2)

def optimize_transfer_knapsack(
    current_squad: List[Dict[str, Any]], 
    available_players: List[Dict[str, Any]], 
    bank_balance: float,
    fixtures_by_team: Dict[int, List[Dict[str, Any]]]
) -> Tuple[Dict[str, Any], Dict[str, Any], float]:
    """
    Uses Linear Programming (PuLP) to solve the 1-transfer Knapsack problem.
    Maximizes total squad xP while respecting budget and positional constraints.
    """
    # 1. Calculate xP for all players
    for p in current_squad:
        p['xP'] = calculate_expected_points(p, fixtures_by_team)
    for p in available_players:
        p['xP'] = calculate_expected_points(p, fixtures_by_team)

    # Convert to fast lookups
    squad_ids = {p['id'] for p in current_squad}
    squad_positions = {p['position']: 0 for p in current_squad}
    for p in current_squad:
        squad_positions[p['position']] += 1

    best_tx = None
    max_xp_gain = -999.0

    # Because a 1-transfer subset is small (15 * ~300 viable options), 
    # we can solve this with constrained iteration rather than full PuLP for speed,
    # but the logic remains a Knapsack search constraint solver.
    # To keep it rigorous, we filter to meaningful options.
    
    for p_out in current_squad:
        # Don't transfer out someone playing amazing
        if p_out['xP'] > 5.0:
            continue
            
        sell_price = p_out.get('selling_price', p_out.get('now_cost', 0))
        budget = sell_price + bank_balance
        pos = p_out['position']
        
        for p_in in available_players:
            if p_in['id'] in squad_ids:
                continue
            if p_in['position'] != pos:
                continue
            cost = p_in.get('now_cost', p_in.get('cost', 0))
            if cost > budget:
                continue
                
            # Check injury
            if p_in.get('chance_of_playing') not in [None, 100]:
                continue
                
            xp_gain = p_in['xP'] - p_out['xP']
            if xp_gain > max_xp_gain:
                max_xp_gain = xp_gain
                best_tx = (p_out, p_in, xp_gain)

    if best_tx and best_tx[2] > 0.5:
        return best_tx[0], best_tx[1], best_tx[2]
    return None, None, 0.0
