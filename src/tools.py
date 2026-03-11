from langchain_core.tools import tool
from typing import List, Dict, Any
from .fpl_client import FPLClient
import logging

logger = logging.getLogger(__name__)

# Note: Since LangChain tools usually take simple args or rely on global state,
# we need to pass a context or instantiate these inside an environment where FPLClient is available,
# or we can just initialize an FPLClient safely inside the tool.

_client = FPLClient()

@tool
def find_affordable_replacements(position: str, selling_player_id: int, bank_balance: float, current_gameweek: int, team_id: int) -> str:
    """
    Calculates the exact selling price of the player you want to sell (accounting for the 50% profit rule)
    and returns a list of target replacements that play the requested position and cost less than or equal
    to (selling_price + bank_balance).

    Args:
        position: String, e.g. "GK", "DEF", "MID", "FWD".
        selling_player_id: Integer, the FPL ID of the player you are transferring out.
        bank_balance: Float, the current bank balance of the manager (in millions, e.g., 1.5).
        current_gameweek: Integer, the latest gameweek we are heading into.
        team_id: Integer, the user's FPL manager ID.
    
    Returns:
        A Markdown-formatted string with the list of affordable replacement options.
    """
    try:
        bootstrap_data = _client.get_bootstrap_static()
        elements = bootstrap_data.get('elements', [])
        element_types = {et['id']: et['singular_name_short'] for et in bootstrap_data.get('element_types', [])}
        
        # 1. Fetch current gameweek picks for the user to determine the 'purchase_price'
        picks_data = _client.get_manager_picks(team_id, current_gameweek - 1)
        my_picks = picks_data.get('picks', [])
        
        # Find the selling player in my picks
        target_pick = next((p for p in my_picks if p['element'] == selling_player_id), None)
        if not target_pick:
            return f"Error: Player ID {selling_player_id} is not in your current squad."
            
        # According to FPL rules, exact selling price depends on purchase price.
        # But wait, in the 'picks' endpoint, the API provides 'selling_price' directly!
        selling_price_raw = target_pick.get('selling_price')
        if selling_price_raw is not None:
            selling_price = float(selling_price_raw) / 10.0
        else:
            # Fallback if selling_price is not in picks api (sometimes FPL changes payload)
            # Find current price
            selling_element = next((e for e in elements if e['id'] == selling_player_id), None)
            if not selling_element:
                return "Error: Could not find player info."
            selling_price = float(selling_element['now_cost']) / 10.0
            
        max_affordable_price = selling_price + bank_balance
        
        # 2. Filter available players
        # Keep players of the requested position who cost <= max_affordable_price
        affordable_options = []
        for element in elements:
            player_pos = element_types.get(element['element_type'])
            cost = float(element['now_cost']) / 10.0
            
            # Simple heuristic filters: 
            # - Play the right position
            # - Are affordable
            # - Not the player we are selling
            # - Played some minutes or have some total points (to remove complete benchwarmers)
            if player_pos == position and cost <= max_affordable_price and element['id'] != selling_player_id:
                if element['total_points'] > 30 and element['chance_of_playing_next_round'] in [None, 100]:
                    affordable_options.append({
                        'id': element['id'],
                        'name': element['web_name'],
                        'cost': cost,
                        'total_points': element['total_points'],
                        'form': element['form'],
                    })
                    
        # Sort by total points (or form) as a quick heuristic
        affordable_options.sort(key=lambda x: x['total_points'], reverse=True)
        top_options = affordable_options[:15] # Top 15 options
        
        out = f"**Selling Price of Player {selling_player_id}**: {selling_price}m\n"
        out += f"**Max Replacement Budget**: {max_affordable_price}m\n\n"
        out += f"**Top Affordable {position} Options:**\n"
        for opt in top_options:
            out += f"- {opt['name']} (ID: {opt['id']}): {opt['cost']}m | Form: {opt['form']} | Pts: {opt['total_points']}\n"
            
        return out

    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return f"Warning: Failed to execute tool find_affordable_replacements. Error: {str(e)}"
