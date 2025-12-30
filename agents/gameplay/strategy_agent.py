from typing import Optional, List
from agents.interfaces.game_agent import BaseGameAgent
from engine.core.game import Game
from engine.state import GameState
from engine.core.actions import GameAction
from engine.ai.evaluator import GameEvaluator
import copy

class StrategyAgent(BaseGameAgent):
    def __init__(self, id: str, name: str = "Strategy Bot"):
        super().__init__(id, name)
        self.evaluator = GameEvaluator()

    def take_action(self, game_state: GameState, valid_actions: List[GameAction]) -> GameAction:
        if not valid_actions:
            # Should not happen if engine is correct, but safe fallback
            return None
            
        # Debug Life
        # pid = list(game_state.players.keys())[1]
        # p_life = len(game_state.players[pid].life)
        # print(f"[StrategyAgent Debug] Real P2 Life: {p_life}")
                
        # Greedy Approach: Simulate each action and pick the one with highest score
        best_score = float('-inf')
        best_action = valid_actions[0] # Default to first action
        
        # Optimization: Filter duplicates if necessary
        
        for action in valid_actions:
            try:
                # 1. Clone State
                simulated_state = copy.deepcopy(game_state)
                # pid = list(simulated_state.players.keys())[1]
                # print(f"[StrategyAgent Debug] Sim P2 Life: {len(simulated_state.players[pid].life)}")
                
                # 2. Setup Sim Engine
                # We need to reconstruct players from state to init Game
                # GameState doesn't have player_order, so we just grab values.
                # Assuming 2 players.
                players = list(simulated_state.players.values())
                p1 = players[0]
                p2 = players[1] if len(players) > 1 else players[0] # Fallback
                
                sim_game = Game(p1, p2)
                sim_game.state = simulated_state
                
                pid = list(simulated_state.players.keys())[1]
                p2_obj = simulated_state.players[pid]
                print(f"[Sim Debug] P2 Life Before Action: {len(p2_obj.life)} | ID: {id(p2_obj)}")
                
                # 3. Process Action
                sim_game.process_action(action)
                
                # SPECIAL HANDLING: If Action caused a Battle, resolve it to see the outcome!
                # Otherwise "Attacking" has no value (just rests unit).
                if sim_game.state.current_battle:
                     # While we are in battle, play it out.
                     # For GREEDY simulation, let's assume opponent NO_BLOCK / NO_COUNTER (Passes).
                     # This gives us the "Optimistic" value of the attack.
                     
                     limit = 0
                     while sim_game.state.current_battle and limit < 5:
                         battle_phase = sim_game.state.current_battle
                         # Whose turn to act?
                         actor_id = None
                         if battle_phase.current_step == 'BLOCK':
                             actor_id = sim_game.state.get_opponent(battle_phase.attacker_id).id
                         elif battle_phase.current_step == 'COUNTER':
                              actor_id = sim_game.state.get_opponent(battle_phase.attacker_id).id
                         
                         if actor_id:
                             # Force Pass (ResolveBattleAction)
                             from engine.core.actions import ResolveBattleAction
                             sim_game.process_action(ResolveBattleAction(player_id=actor_id, action_type='RESOLVE_BATTLE'))
                         else:
                             break
                         limit += 1
                
                # 4. Evaluate
                # We evaluate from OUR perspective (self.id)
                score = self.evaluator.evaluate(sim_game.state, self.id)
                
                # Debug print
                # print(f"Action {action.action_type} -> Score {score}")
                
                if score > best_score:
                    best_score = score
                    best_action = action
                    
            except Exception as e:
                # If simulation fails, skip this action
                # print(f"[StrategyAgent] Simulation Error for {action}: {e}")
                continue
                
        return best_action
