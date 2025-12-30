
import json
import os
from typing import List, Tuple, Dict
from engine.models.card import Card, CardInstance
from engine.models.player import Player

def load_card_db(clean_json_dir: str) -> Dict[str, dict]:
    """
    Loads all JSON files from the directory into a single dictionary mapping ID -> Card Data.
    """
    card_db = {}
    if not os.path.exists(clean_json_dir):
        print(f"Warning: Directory {clean_json_dir} does not exist.")
        return card_db

    for filename in os.listdir(clean_json_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(clean_json_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for card in data:
                            if 'id' in card:
                                card_db[card['id']] = card
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return card_db

def load_deck_from_json(deck_file_path: str, card_db: Dict[str, dict]) -> Tuple[Card, List[Card]]:
    """
    Parses a Deck JSON file and returns (Leader Card Object, List of Deck Card Objects).
    """
    if not os.path.exists(deck_file_path):
        raise ValueError(f"Deck file not found: {deck_file_path}")

    with open(deck_file_path, 'r', encoding='utf-8') as f:
        deck_data = json.load(f)

    leader_id = deck_data.get("leader")
    if leader_id not in card_db:
        # Fallback for Missing Leader
        print(f"Warning: Leader ID {leader_id} not found. Creating Mock Leader.")
        leader_card = Card(
            id=leader_id,
            name=f"Mock {leader_id}",
            type="LEADER",
            color="UNKNOWN",
            cost=5,
            power=5000,
            life=5, # Standard
            attribute="STRIKE",
            category="LEADER"
        )
    else:
        leader_data = card_db[leader_id]
        # Normalize Enums
        if 'type' in leader_data: leader_data['type'] = leader_data['type'].upper()
        if 'attribute' in leader_data: leader_data['attribute'] = leader_data['attribute'].upper()
        if 'color' in leader_data: leader_data['color'] = leader_data['color'].upper()
        
        leader_card = Card(**leader_data)
    
    deck_cards = []
    
    for entry in deck_data.get("cards", []):
        c_id = entry["id"]
        qty = entry["quantity"]
        
        if c_id not in card_db:
            print(f"Warning: Card ID {c_id} not found in DB. Skipping.")
            continue
            
        card_data = card_db[c_id].copy() # Copy to avoid mutating DB
        
        # Normalize
        if 'type' in card_data: card_data['type'] = card_data['type'].upper()
        if 'attribute' in card_data: 
            raw_attr = card_data['attribute'].upper()
            if ';' in raw_attr:
                raw_attr = raw_attr.split(';')[0] # Take first for now
            card_data['attribute'] = raw_attr
        if 'color' in card_data: card_data['color'] = card_data['color'].upper()

        # Instantiate Card
        try:
            base_card = Card(**card_data)
            for _ in range(qty):
                deck_cards.append(base_card) 
        except Exception as e:
            print(f"Error instantiating card {c_id}: {e}")
            continue
            
    return leader_card, deck_cards
