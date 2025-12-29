import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.models.player import Player
from engine.models.card import Card, CardInstance
from engine.core.game import Game
from agents.gameplay.random_agent import RandomAgent
from agents.gameplay.rule_based_agent import SimpleRuleAgent

def create_dummy_deck() -> list[Card]:
    """Create a simple deck for testing"""
    deck = []
    # 40 Characters, 10 Events (Simplified)
    for i in range(50):
        c = Card(
            id=f"OP01-{i:03d}", 
            name=f"Card {i}", 
            type="CHARACTER", 
            cost=2, 
            power=5000,
            colors=["RED"]
        )
        deck.append(c)
    return deck

def create_dummy_leader(id: str, name: str) -> CardInstance:
    """Create a dummy leader instance"""
    leader_card = Card(id=id, name=name, type="LEADER", life=5, colors=["RED"])
    return CardInstance(
        card_id=leader_card.id,
        instance_id=f"{id}_leader",
        owner_id=id,
        current_power=5000
    )

def run_simulation(max_turns=20):
    print("=== OPTCG Agent Simulation (Random vs RuleBased) ===\n")
    
    # 1. Setup Agents & Players
    agent1 = RandomAgent(id="p1", name="Bot Luffy (Random)")
    agent2 = SimpleRuleAgent(id="p2", name="Bot Kaido (RuleBased)")
    
    p1 = Player(id="p1", name="Bot Luffy (Random)", deck=create_dummy_deck())
    p2 = Player(id="p2", name="Bot Kaido (RuleBased)", deck=create_dummy_deck())
    
    # Assign Leaders
    p1.leader = create_dummy_leader("leader_luffy", "Monkey D. Luffy")
    p2.leader = create_dummy_leader("leader_kaido", "Kaido")

    # 2. Start Game
    game = Game(p1, p2)
    game.start_game()
    print(f"Game Started! {p1.name} vs {p2.name}")
    
    # 3. Game Loop
    agents = { "p1": agent1, "p2": agent2 }
    
    while game.state.turn_count <= max_turns:
        current_player_id = game.state.active_player_id
        active_agent = agents[current_player_id]
        
        print(f"\n--- Turn {game.state.turn_count} | Phase: {game.state.current_phase} | Player: {active_agent.name} ---")
        
        # 1. Check for winner
        if game.state.winner_id:
            print(f">>> WINNER: {game.state.winner_id} <<<")
            break

        # 2. Get Valid Actions from Engine
        valid_actions = game.get_valid_actions()
        print(f"Valid Actions ({len(valid_actions)}): {[a.action_type for a in valid_actions]}")
        
        # 3. Agent Decides
        action = active_agent.take_action(game.state, valid_actions)
        print(f"Agent Chose: {action.action_type}")
        if action.action_type == 'PLAY_CARD':
             print(f"  -> Card Index: {action.card_hand_index}")
        elif action.action_type == 'ATTACK':
             print(f"  -> Target: {action.target_instance_id}")

        # 4. Engine Executes
        success = game.process_action(action)
        if not success:
            print("!!! Action Failed (Should not happen with Valid Actions) !!!")
            break
            
        # Optional: Sleep for visualization
        # time.sleep(0.5)
        
    print("\n=== Simulation Ended ===")

if __name__ == "__main__":
    run_simulation()
