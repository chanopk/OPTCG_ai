
import os
import sys
import time
from collections import defaultdict
from engine.core.game import Game
from engine.models.player import Player
from engine.models.card import CardInstance
from agents.gameplay.strategy_agent import StrategyAgent
from engine.utils.deck_loader import load_card_db, load_deck_from_json

def run_simulation(p1_deck_file, p2_deck_file, num_games=10, verbose=False):
    # 1. Load Database
    project_root = os.getcwd() # Assumption: Run from root
    db_path = os.path.join(project_root, "data/clean_json")
    if verbose: print("Loading Card Database...")
    card_db = load_card_db(db_path)
    if verbose: print(f"Database Loaded: {len(card_db)} cards.")

    # 2. Load Decks
    if verbose: print(f"Loading Player 1 Deck: {p1_deck_file}")
    l1, d1 = load_deck_from_json(p1_deck_file, card_db)
    
    if verbose: print(f"Loading Player 2 Deck: {p2_deck_file}")
    l2, d2 = load_deck_from_json(p2_deck_file, card_db)

    print("-" * 50)
    print(f"P1 Leader: {l1.name} ({l1.id})")
    print(f"P2 Leader: {l2.name} ({l2.id})")
    print(f"Games: {num_games}")
    print("-" * 50)

    # 3. Setup Agents
    # Both use StrategyAgent for fairness
    agent1 = StrategyAgent(id="p1", name="P1 (Strategy)")
    agent2 = StrategyAgent(id="p2", name="P2 (Strategy)")
    
    # Stats
    wins = {"p1": 0, "p2": 0}
    
    for i in range(num_games):
        if verbose: print(f"\n=== Game {i+1}/{num_games} ===")
        
        # Fresh Lists
        p1_list = d1[:]
        p2_list = d2[:]
        
        # Init Players (Corrected CardInstance kwargs)
        player1 = Player(id="p1", name="Player 1", deck=p1_list, life=[])
        player1.leader = CardInstance(
            card_id=l1.id, 
            instance_id="p1_leader", 
            owner_id="p1", 
            current_power=l1.power
        )
        
        player2 = Player(id="p2", name="Player 2", deck=p2_list, life=[])
        player2.leader = CardInstance(
            card_id=l2.id, 
            instance_id="p2_leader", 
            owner_id="p2", 
            current_power=l2.power
        )
        
        # Init Game
        game = Game(player1, player2)
        game.start_game()
        
        # Agents Map
        agents = { "p1": agent1, "p2": agent2 }
        
        turn_count = 0
        while not game.state.winner_id and turn_count < 100:
            current_pid = game.state.active_player_id
            active_agent = agents[current_pid]
            
            # Logging State
            if verbose:
                p1_info = f"Life:{len(game.state.players['p1'].life)} Hand:{len(game.state.players['p1'].hand)} Field:{len(game.state.players['p1'].field.character_area)}"
                p2_info = f"Life:{len(game.state.players['p2'].life)} Hand:{len(game.state.players['p2'].hand)} Field:{len(game.state.players['p2'].field.character_area)}"
                print(f"\n[Turn {turn_count}] Active: {current_pid} | {p1_info} vs {p2_info}")
            
            # Get Action
            valid_actions = game.get_valid_actions()
            action = active_agent.take_action(game.state, valid_actions)
            
            if not action:
                print(f"Error: {current_pid} returned no action.")
                break
            
            if verbose:
                print(f"Action: {action}")

            # Execute
            success = game.process_action(action)
            if not success:
               print(f"Error: Action failed {action}")
               break
               
            if action.action_type == 'END_PHASE':
                turn_count += 1
                if not verbose and turn_count % 10 == 0:
                     sys.stdout.write('.')
                     sys.stdout.flush()

        winner = game.state.winner_id
        if winner:
            wins[winner] += 1
            if verbose: print(f"  Result: {winner} Wins!")
        else:
            if verbose: print("  Result: Draw")

    print("\n" + "=" * 50)
    print(f"FINAL RESULTS: {num_games} Games")
    print(f"Player 1 ({os.path.basename(p1_deck_file)}): {wins['p1']} Wins ({(wins['p1']/num_games)*100}%)")
    print(f"Player 2 ({os.path.basename(p2_deck_file)}): {wins['p2']} Wins ({(wins['p2']/num_games)*100}%)")
    print("=" * 50)

if __name__ == "__main__":
    p1 = "engine/data/deck/OP11_luffy.json"
    p2 = "engine/data/deck/OP14_mihawk.json"
    
    # Run 1 Game in Verbose Mode
    run_simulation(p1, p2, num_games=1, verbose=True)
