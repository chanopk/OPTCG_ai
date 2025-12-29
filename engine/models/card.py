from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from engine.models.effect import Effect

# Constants for Card Types and Attributes
CardType = Literal['LEADER', 'CHARACTER', 'EVENT', 'STAGE', 'DON']
CardColor = Literal['RED', 'GREEN', 'BLUE', 'PURPLE', 'BLACK', 'YELLOW']
CardAttribute = Literal['STRIKE', 'SLASH', 'SPECIAL', 'WISDOM', 'RANGED']

class CardEffect(BaseModel):
    """
    Represents a parsed effect of a card.
    For now, we store the raw text and a type.
    Future iterations will include structured trigger/action data.
    """
    trigger: str  # e.g., "On Play", "When Attacking"
    effect_text: str

class Card(BaseModel):
    """
    Base model for all One Piece TCG cards.
    """
    id: str = Field(..., description="Card ID e.g., 'OP01-001'")
    name: str
    type: CardType
    colors: List[CardColor] = Field(default_factory=list)
    
    # Stats (Optional because Events/Stages/Don don't have all of them)
    cost: int = 0
    power: int = 0
    counter: int = 0
    attribute: Optional[CardAttribute] = None
    
    # Text interactions
    effects: List[CardEffect] = Field(default_factory=list) # Raw Text
    effect_list: List[Effect] = Field(default_factory=list, description="Structured effects for Engine")
    tags: List[str] = Field(default_factory=list, description="Type tags e.g., 'Supernovas', 'Straw Hat Crew'")
    
    # Image (Optional)
    image_url: Optional[str] = None

    class Config:
        frozen = True # Cards are immutable definitions

class CardInstance(BaseModel):
    """
    Represents a specific card in play (on the field).
    """
    card_id: str = Field(..., description="Reference to the Card Definition ID")
    instance_id: str = Field(..., description="Unique ID for this specific instance in the game")
    owner_id: str
    
    # State
    is_rested: bool = False
    current_power: int = 0 # Base power + boosts
    attached_don: int = 0
    
    # Temporary modifiers (e.g. from effects)
    power_modifier: int = 0
    cost_modifier: int = 0
    granted_keywords: List[str] = Field(default_factory=list) # e.g. RUSH, BLOCKER
    
    @property
    def total_power(self) -> int:
        return self.current_power + self.power_modifier + (self.attached_don * 1000)
