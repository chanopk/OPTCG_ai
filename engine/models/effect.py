from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel

class EffectType(str, Enum):
    ON_PLAY = "ON_PLAY"
    WHEN_ATTACKING = "WHEN_ATTACKING"
    ACTIVATE_MAIN = "ACTIVATE_MAIN"
    TRIGGER = "TRIGGER"
    BLOCKER = "BLOCKER"
    RUSH = "RUSH"
    BANISH = "BANISH"
    DOUBLE_ATTACK = "DOUBLE_ATTACK"
    DRAW_CARD = "DRAW_CARD"
    TRASH_CARD = "TRASH_CARD"
    RETURN_TO_HAND = "RETURN_TO_HAND"
    RETURN_TO_BOTTOM_DECK = "RETURN_TO_BOTTOM_DECK"
    COST_CHANGE = "COST_CHANGE"
    SET_ACTIVE = "SET_ACTIVE"
    # DON_MINUS handled via condition_cost
    
    # Generic Actions
    KO_CHARACTER = "KO_CHARACTER"
    BUFF_POWER = "BUFF_POWER"

class Effect(BaseModel):
    """
    Structured definition of a card effect.
    """
    type: EffectType
    
    # Conditions
    condition_don: int = 0  # Requires attached Don!! (e.g., Don!! x1)
    condition_cost: int = 0 # Requires paying cost (e.g., Don!! -1)
    
    # Targeting
    target_filter: Optional[str] = None # DSL-like string e.g., "opponent|character|rested|cost<=4"
    
    # Action Payload
    action_code: EffectType # What happens?
    action_power: int = 0 # For buffs
    action_value: int = 0 # For generic values
    
    description: str = "" # Human readable text
