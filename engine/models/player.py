from typing import List, Optional
from pydantic import BaseModel, Field
from engine.models.card import Card, CardInstance
from engine.models.field import FieldArea

class Player(BaseModel):
    """
    Represents a Player in the game.
    """
    id: str
    name: str
    
    # Resources
    # Note: explicit Field(default_factory=list) is required to avoid shared mutable defaults
    life: List[Card] = Field(default_factory=list) 
    hand: List[Card] = Field(default_factory=list)
    deck: List[Card] = Field(default_factory=list) 
    trash: List[Card] = Field(default_factory=list)
    
    # Field State
    field: FieldArea = Field(default_factory=FieldArea)
    leader: Optional[CardInstance] = None
    
    # Don!! Resources
    cost_area: List[str] = Field(default_factory=list) # List of Don Card IDs (simplified) or Objects
    active_don: int = 0
    rested_don: int = 0
    attached_don: int = 0 # Don attached to characters/leader
    
    # Logic methods can be added here or in Game Controller
    def draw_card(self, amount: int = 1):
        for _ in range(amount):
            if self.deck:
                card = self.deck.pop(0)
                self.hand.append(card)
            else:
                # Deck out logic (Lose game?)
                pass
