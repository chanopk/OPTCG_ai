from abc import ABC, abstractmethod
from engine.state import GameState
from engine.core.actions import GameAction

class BaseGameAgent(ABC):
    """
    Abstract base class for all Gameplay Agents.
    """
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        
    @abstractmethod
    def take_action(self, game_state: GameState, valid_actions: list[GameAction]) -> GameAction:
        """
        Decide on an action to take based on the current game state.
        """
        pass
