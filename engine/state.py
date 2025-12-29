from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field
from engine.models.player import Player
from engine.core.battle import BattlePhase

PhaseType = Literal['REFRESH_PHASE', 'DRAW_PHASE', 'DON_PHASE', 'MAIN_PHASE', 'END_PHASE']

class GameState(BaseModel):
    """
    Represents the entire state of the game at a specific moment.
    This is what will be fed into the AI Agent.
    """
    turn_count: int = 1
    current_phase: PhaseType = 'REFRESH_PHASE'
    active_player_id: str
    winner_id: str | None = None
    
    # Battle State (Transient)
    current_battle: Optional[BattlePhase] = None
    
    # Players map by ID
    players: Dict[str, Player] = Field(default_factory=dict)
    
    def get_active_player(self) -> Player:
        return self.players[self.active_player_id]
        
    def get_opponent(self, player_id: str) -> Player:
        for pid, p in self.players.items():
            if pid != player_id:
                return p
        raise ValueError("Opponent not found")
