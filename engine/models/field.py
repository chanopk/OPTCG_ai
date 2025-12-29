from typing import List, Optional
from pydantic import BaseModel, Field
from engine.models.card import CardInstance

class FieldArea(BaseModel):
    """
    Represents the play area (Board) of a single player.
    """
    character_area: List[CardInstance] = Field(default_factory=list, description="Max 5 characters")
    stage_area: Optional[CardInstance] = None
    
    # Check limits
    def add_character(self, character: CardInstance):
        if len(self.character_area) >= 5:
            raise ValueError("Character area is full (Max 5)")
        self.character_area.append(character)
        
    def remove_character(self, instance_id: str) -> Optional[CardInstance]:
        for i, char in enumerate(self.character_area):
            if char.instance_id == instance_id:
                return self.character_area.pop(i)
        return None
