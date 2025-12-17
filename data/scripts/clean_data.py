
import json
import os
import re

# Define input and output directories
# Adjusted paths since we are now in data/clean_data.py (or running from root)
# If running from root: data/raw_json
INPUT_DIR = r"d:\ai project\OPTCG_ai\data\raw_json"
OUTPUT_DIR = r"d:\ai project\OPTCG_ai\data\clean_json"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_int(value):
    """Safely converts a value to int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def clean_name(name, card_number):
    """
    Cleans the name by removing the card number if it's derived from the raw format.
    Example: "Crocodile - OP14-079" -> "Crocodile"
    """
    if not name:
        return ""
    # Remove the specific pattern " - {card_number}" if present
    if card_number and card_number in name:
        # Check for typical "Name - Number" pattern
        pattern = f"\\s*-\\s*{re.escape(card_number)}"
        cleaned = re.sub(pattern, "", name)
        return cleaned.strip()
    
    # Fallback: sometimes the suffix isn't exactly the number, or format varies.
    # But usually cleanName provided by TCGPlayer is not always perfect either (e.g. "Crocodile OP14 079").
    # If the user wants strictly just the name, we might rely on the part before " - " if it exists.
    if " - " in name:
        return name.split(" - ")[0].strip()
        
    return name

def parse_card(raw_card):
    """Parses a single raw card dictionary into the optimized format."""
    
    # Extract extended data into a dictionary for easier access
    ext_data = {item['name']: item['value'] for item in raw_card.get('extendedData', [])}

    # Extract Card Number (Primary ID)
    card_id = ext_data.get('Number')
    if not card_id:
        # Fallback if Number is missing? (Should not happen for valid cards)
        return None

    # Basic fields
    name = raw_card.get('name', '')
    cleaned_name = clean_name(name, card_id)

    # Attributes
    color = ext_data.get('Color')
    card_type = ext_data.get('CardType')
    attribute = ext_data.get('Attribute') # Special, Slash, etc.
    
    # Numeric fields
    power = safe_int(ext_data.get('Power'))
    life = safe_int(ext_data.get('Life'))
    cost = safe_int(ext_data.get('Cost'))
    counter = safe_int(ext_data.get('Counterplus')) 

    rarity = ext_data.get('Rarity')
    
    # Subtypes (semicolon separated)
    subtypes_raw = ext_data.get('Subtypes', '')
    subtypes = [s.strip() for s in subtypes_raw.split(';')] if subtypes_raw else []

    # Effect text
    description = ext_data.get('Description', '')

    # Build optimized object
    optimized_card = {
        "id": card_id,
        "name": cleaned_name,
        "type": card_type,
        "color": color,
        "attribute": attribute,
        "power": power,
        "life": life,
        "counter": counter,
        "cost": cost,
        "rarity": rarity,
        "subtypes": subtypes,
        "effect": description
    }

    return {k: v for k, v in optimized_card.items() if v is not None and v != ""}

def process_files():
    print(f"Reading from: {INPUT_DIR}")
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory {INPUT_DIR} not found.")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    
    for filename in files:
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            if not isinstance(raw_data, list):
                print(f"Skipping {filename}: Root is not a list.")
                continue

            cleaned_cards = []
            for item in raw_data:
                cleaned = parse_card(item)
                if cleaned:
                    cleaned_cards.append(cleaned)
            
            if cleaned_cards:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_cards, f, ensure_ascii=False, indent=2)
                print(f"Processed {filename}: {len(cleaned_cards)} cards.")
            else:
                print(f"No valid cards found in {filename}.")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    process_files()
