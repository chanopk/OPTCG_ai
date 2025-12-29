import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models.player import Player
from engine.models.card import Card
from engine.core.game import Game
from engine.core.actions import PlayCardAction

def run_simulation():
    print("=== OPTCG Game Engine Simulation ===\n")
    
    # 1. Setup Players
    p1 = Player(id="p1", name="Luffy")
    p2 = Player(id="p2", name="Kaido")
    
    # 2. Add Cards to Hand
    zoro = Card(
        id="OP01-025", 
        name="Roronoa Zoro", 
        type="CHARACTER", 
        cost=3, 
        power=5000, 
        colors=["RED"], 
        attribute="SLASH"
    )
    p1.hand.append(zoro)
    print(f"Player 1 Hand: {[c.name for c in p1.hand]}")
    
    # 3. Start Game
    game = Game(p1, p2)
    print(f"Game Started. Active Player: {game.state.get_active_player().name}")
    print(f"Current Phase: {game.state.current_phase}")
    
    # 4. Advance to Main Phase
    print("\n--- Advancing to Main Phase ---")
    while game.state.current_phase != "MAIN_PHASE":
        game._handle_end_phase()
        print(f"Phase Changed: {game.state.current_phase}")
        
    print(f"Active Player: {game.state.get_active_player().name}")
    
    # 5. Play Card
    print("\n--- Action: Play Card (Zoro) ---")
    action = PlayCardAction(player_id="p1", card_hand_index=0)
    success = game.process_action(action)
    
    if success:
        print(">> Action Successful!")
        print(f"Player 1 Field: {[c.card_id for c in p1.field.character_area]}")
        print(f"Player 1 Hand: {len(p1.hand)}")
    else:
        print(">> Action Failed!")
        
    # 6. End Turn
    print("\n--- Ending Turn ---")
    game._handle_end_phase() # End Main
    game._handle_end_phase() # End End -> Refresh (Next Turn)
    
    print(f"Turn Count: {game.state.turn_count}")
    print(f"Active Player: {game.state.get_active_player().name}")
    print(f"Current Phase: {game.state.current_phase}")
    
    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    run_simulation()
