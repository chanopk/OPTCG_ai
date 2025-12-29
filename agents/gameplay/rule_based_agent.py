from agents.interfaces.game_agent import BaseGameAgent
from engine.state import GameState
from engine.core.actions import GameAction, PlayCardAction, AttackAction

class SimpleRuleAgent(BaseGameAgent):
    """
    A rule-based agent that follows simple heuristics:
    1. Attack: If can attack and Power >= Target Power, do it. Prioritize winning attacks.
    2. Play: Play the highest cost card possible.
    3. End: Otherwise end turn.
    """
    def take_action(self, game_state: GameState, valid_actions: list[GameAction]) -> GameAction:
        if not valid_actions:
             # Should not happen as EndPhase is always there
             raise ValueError("No valid actions!")

        active_player = game_state.get_active_player()
        opponent = game_state.get_opponent(active_player.id)

        # 1. Check for Attacks
        attack_actions = [a for a in valid_actions if a.action_type == 'ATTACK']
        if attack_actions:
            # Sort/Filter for efficient attacks
            # We want attacks where Attacker Power >= Target Power
            favorable_attacks = []
            
            for action in attack_actions:
                if isinstance(action, AttackAction):
                    # Resolve Attacker
                    attacker = None
                    if active_player.leader and active_player.leader.instance_id == action.attacker_instance_id:
                        attacker = active_player.leader
                    else:
                        for char in active_player.field.character_area:
                            if char.instance_id == action.attacker_instance_id:
                                attacker = char
                                break
                    
                    # Resolve Target
                    target = None
                    if opponent.leader and opponent.leader.instance_id == action.target_instance_id:
                        target = opponent.leader
                    else:
                        for char in opponent.field.character_area:
                            if char.instance_id == action.target_instance_id:
                                target = char
                                break
                    
                    if attacker and target:
                        # Heuristic: Attack if Power >= Target
                        if attacker.total_power >= target.total_power:
                            # Priority Score: 
                            # Attack Leader (2) > Attack Character (1)
                            score = 2 if target.instance_id == opponent.leader.instance_id else 1
                            favorable_attacks.append((score, action))
            
            if favorable_attacks:
                # Sort by score descending
                favorable_attacks.sort(key=lambda x: x[0], reverse=True)
                return favorable_attacks[0][1]

        # 2. Check for Play Cards
        play_actions = [a for a in valid_actions if a.action_type == 'PLAY_CARD']
        if play_actions:
            # Play Max Cost Card
            sorted_play_actions = []
            for action in play_actions:
                if isinstance(action, PlayCardAction):
                    card = active_player.hand[action.card_hand_index]
                    sorted_play_actions.append((card.cost, action))
            
            if sorted_play_actions:
                sorted_play_actions.sort(key=lambda x: x[0], reverse=True)
                return sorted_play_actions[0][1]

        # 3. Default: End Phase
        # Find End Phase Action
        for action in valid_actions:
            if action.action_type == 'END_PHASE':
                return action
                
        return valid_actions[0]
