from typing import Optional, List
from pydantic import BaseModel
from engine.models.card import CardInstance

class BattlePhase(BaseModel):
    """
    State of the current battle.
    """
    attacker_id: str
    attacker_instance_id: str
    target_instance_id: str
    
    # Steps: DECLARE -> BLOCK -> COUNTER -> DAMAGE -> RESOLVE
    current_step: str = "DECLARE" 
    
    # Stats snapshot
    attacker_power: int = 0
    target_power: int = 0
    
    # Modifiers
    blocker_instance_id: Optional[str] = None
    counter_cards: List[str] = [] # Cards discarded for counter
    counter_power_bonus: int = 0
