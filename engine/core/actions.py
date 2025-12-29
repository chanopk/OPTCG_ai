from typing import Optional, Literal
from pydantic import BaseModel, Field

ActionType = Literal['PLAY_CARD', 'ATTACK', 'ACTIVATE_EFFECT', 'END_PHASE', 'BLOCK', 'COUNTER', 'RESOLVE_BATTLE']

class GameAction(BaseModel):
    """
    Base class for any action a player can take.
    """
    player_id: str
    action_type: ActionType

class PlayCardAction(GameAction):
    action_type: Literal['PLAY_CARD'] = 'PLAY_CARD'
    card_hand_index: int
    target_area: Literal['CHARACTER', 'STAGE'] = 'CHARACTER'

class AttackAction(GameAction):
    action_type: Literal['ATTACK'] = 'ATTACK'
    attacker_instance_id: str
    target_instance_id: str # Can be Character or Leader
    attached_don: int = 0 # Don!! added for this attack (from active Don)

class BlockAction(GameAction):
    action_type: Literal['BLOCK'] = 'BLOCK'
    blocker_instance_id: str # Character with Blocker trait

class CounterAction(GameAction):
    action_type: Literal['COUNTER'] = 'COUNTER'
    card_hand_index: int # Card to discard for counter

class ResolveBattleAction(GameAction):
     action_type: Literal['RESOLVE_BATTLE'] = 'RESOLVE_BATTLE' # System action or automatic?

class EndTurnAction(GameAction):
    action_type: Literal['END_PHASE'] = 'END_PHASE'
