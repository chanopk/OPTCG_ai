import os
import json
from typing import List, Dict, Optional
from engine.models.card import Card, CardType, CardColor, CardAttribute
from engine.data.parser import EffectParser

class CardLoader:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.parser = EffectParser()
        self.cards: Dict[str, Card] = {}
        
    def load_all_cards(self) -> List[Card]:
        """
        Iterates over all JSON files in the data directory and loads cards.
        """
        loaded_cards = []
        
        if not os.path.exists(self.data_dir):
            print(f"Directory not found: {self.data_dir}")
            return []
            
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Data can be a list or a dict?
                        # Based on inspection, it's a list of card objects.
                        if isinstance(data, list):
                            for card_data in data:
                                card = self._parse_card_json(card_data)
                                if card:
                                    self.cards[card.id] = card
                                    loaded_cards.append(card)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    
        print(f"Loaded {len(loaded_cards)} cards total.")
        return loaded_cards

    def _parse_card_json(self, data: dict) -> Optional[Card]:
        """
        Converts a JSON dict to a Card object.
        """
        try:
            # Basic mapping
            c_id = data.get("id")
            name = data.get("name")
            
            # Map Type
            raw_type = data.get("type", "Character")
            c_type = self._map_type(raw_type)
            
            # Map Color
            raw_color = data.get("color", "Red")
            colors = self._split_colors(raw_color) # Could be "Red/Green"
            
            # Map Attribute
            raw_attr = data.get("attribute")
            attribute = None
            if raw_attr:
                 # Map to Enum if possible, else None or String?
                 # Enum: Strike, Slash, Ranged, Wisdom, Special
                 attribute = raw_attr if raw_attr in ["Strike", "Slash", "Ranged", "Wisdom", "Special"] else None
            
            # Stats
            power = data.get("power", 0)
            cost = data.get("cost", 0)
            life = data.get("life", 0)
            counter = data.get("counter", 0)
            
            # Effects
            effect_text = data.get("effect", "")
            parsed_effects = self.parser.parse_effects(effect_text)
            
            card = Card(
                id=c_id,
                name=name,
                type=c_type,
                colors=colors,
                attribute=attribute,
                power=power,
                cost=cost,
                life=life,
                counter=counter,
                effect_list=parsed_effects,
                effects=[] # Raw text interactions if needed
            )
            return card
            
        except Exception as e:
            # print(f"Skipping card {data.get('id', 'unknown')}: {e}")
            return None

    def _map_type(self, raw_type: str) -> str:
        # Normalize type
        return raw_type.upper() # LEADER, CHARACTER, EVENT, STAGE

    def _split_colors(self, raw_color: str) -> List[str]:
        # Handle "Red/Green"
        return [c.strip().upper() for c in raw_color.split("/")]
