import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data.loader import CardLoader
from engine.models.effect import EffectType

def main():
    loader = CardLoader("data/clean_json")
    cards = loader.load_all_cards()
    
    total_cards = len(cards)
    cards_with_effects_parsed = 0
    total_effects_parsed = 0
    effects_breakdown = {}
    
    for card in cards:
        if card.effect_list:
            cards_with_effects_parsed += 1
            total_effects_parsed += len(card.effect_list)
            for eff in card.effect_list:
                eff_type = eff.action_code
                effects_breakdown[eff_type] = effects_breakdown.get(eff_type, 0) + 1
                
                # Debug print for specific effects to check quality
                if eff_type == EffectType.KO_CHARACTER:
                     print(f"[Parsed KO] {card.name}: {eff.description} -> Filter: {eff.target_filter}")
    
    print("\n=== Parsing Coverage Report ===")
    print(f"Total Cards Loaded: {total_cards}")
    print(f"Cards with >0 Parsed Effects: {cards_with_effects_parsed}")
    print(f"Total Parsed Effects: {total_effects_parsed}")
    print("\nEffect Type Breakdown:")
    for k, v in effects_breakdown.items():
        print(f"  - {k}: {v}")

if __name__ == "__main__":
    main()
