import random
from agents.interfaces.game_agent import BaseGameAgent
from engine.state import GameState
from engine.core.actions import GameAction

class RandomAgent(BaseGameAgent):
    """
    A basic agent that acts randomly from the list of valid actions.
    Useful for baseline testing and ensuring the Game Engine doesn't crash.
    """
    def take_action(self, game_state: GameState, valid_actions: list[GameAction]) -> GameAction:
        if not valid_actions:
            raise ValueError("No valid actions available! (Should at least have EndPhase)")
            
        # Just pick one!
        chosen_action = random.choice(valid_actions)
        return chosen_action
