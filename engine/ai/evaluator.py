from engine.state import GameState
from engine.models.player import Player

class GameEvaluator:
    def evaluate(self, state: GameState, player_id: str) -> float:
        """
        Evaluate the current game state from the perspective of player_id.
        Higher score = Better position.
        """
        player = state.players[player_id]
        opponent_id = state.get_opponent(player_id).id
        opponent = state.players[opponent_id]
        
        if state.winner_id == player_id:
            return float('inf')
        if state.winner_id == opponent_id:
            return float('-inf')
        
        score = 0.0
        
        # 1. Life Difference (Most Important)
        # Each life point is worth a lot (e.g. 1000)
        score += (len(player.life) - len(opponent.life)) * 1000
        
        # 2. Hand Advantage
        # More options = better
        score += (len(player.hand) - len(opponent.hand)) * 50
        
        # 3. Board Control (Power)
        # Sum of power on board
        my_power = sum(c.current_power + c.power_modifier for c in player.field.character_area)
        # Add Leader power
        my_power += (player.leader.current_power + player.leader.power_modifier)
        
        opp_power = sum(c.current_power + c.power_modifier for c in opponent.field.character_area)
        opp_power += (opponent.leader.current_power + opponent.leader.power_modifier)
        
        score += (my_power - opp_power) * 0.1 # Scale down power value
        
        # 4. Board Control (Units Count)
        score += (len(player.field.character_area) - len(opponent.field.character_area)) * 100
        
        # 5. Key Keywords (Blocker)
        my_blockers = sum(1 for c in player.field.character_area if "BLOCKER" in c.granted_keywords)
        opp_blockers = sum(1 for c in opponent.field.character_area if "BLOCKER" in c.granted_keywords)
        
        score += (my_blockers - opp_blockers) * 300
        
        return score
