from typing import List, Optional
import random
from engine.state import GameState, PhaseType
from engine.core.phases import PhaseManager, Phase
from engine.core.actions import GameAction, PlayCardAction, AttackAction, EndTurnAction
from engine.models.player import Player
from engine.models.card import CardInstance

class Game:
    """
    The main controller for the One Piece Card Game engine.
    Manages state transitions and rule enforcement.
    """
    def __init__(self, player1: Player, player2: Player):
        self.state = GameState(
            active_player_id=player1.id,
            players={
                player1.id: player1,
                player2.id: player2
            }
        )
        self.phase_manager = PhaseManager()
        
    def start_game(self):
        """
        Initial setup: 
        1. Shuffle Decks (Standard 50 cards)
        2. Set Life (Take top cards from deck to life area) - Default 5 or based on Leader
        3. Draw Hand (5 cards)
        """
        for player in self.state.players.values():
            # 1. Shuffle
            random.shuffle(player.deck)
            
            # 2. Set Life (Default 5 for now)
            # In real game, life depends on Leader. We assume 5 if not specified.
            life_points = 5 
            if player.leader:
                life_points = player.leader.life if hasattr(player.leader, 'life') else 5
            
            for _ in range(life_points):
                if player.deck:
                    player.life.append(player.deck.pop(0))
            
            # 3. Draw Hand (5 Cards)
            player.draw_card(amount=5)
        
    def process_action(self, action: GameAction) -> bool:
        """
        Process a player's action. Returns True if valid and executed.
        """
        # 1. Validate Player
        if action.player_id != self.state.active_player_id:
            # Only active player can act during their turn (except Block/Counter - TODO)
            return False
            
        # 2. Handle Action based on Type
        if action.action_type == 'END_PHASE':
            return self._handle_end_phase()
            
        elif action.action_type == 'PLAY_CARD':
            if isinstance(action, PlayCardAction):
                return self._handle_play_card(action)
                
        elif action.action_type == 'ATTACK':
            if isinstance(action, AttackAction):
                return self._handle_attack(action)
                
        return False
        
    def _handle_end_phase(self) -> bool:
        """
        Transition to next phase or next turn.
        """
        current = Phase(self.state.current_phase)
        next_p = self.phase_manager.next_phase(current)
        self.state.current_phase = next_p.value
        
        if next_p == Phase.REFRESH:
            # Switch Turns
            opponent = self.state.get_opponent(self.state.active_player_id)
            self.state.active_player_id = opponent.id
            self.state.turn_count += 1
            # Perform Refresh Phase Logic (Activate Don, Cards)
            self._perform_refresh_phase()
            
        return True
        
    def _handle_play_card(self, action: PlayCardAction) -> bool:
        player = self.state.get_active_player()
        if action.card_hand_index >= len(player.hand):
            return False
            
        # Logic: Move from Hand to Field (Simplified)
        card = player.hand.pop(action.card_hand_index)
        
        # Create Instance
        instance = CardInstance(
            card_id=card.id,
            instance_id=f"{card.id}_{self.state.turn_count}_{len(player.field.character_area)}",
            owner_id=player.id,
            current_power=card.power
        )
        
        try:
            player.field.add_character(instance)
            return True
        except ValueError:
            # Field full
            player.hand.insert(action.card_hand_index, card) # Return to hand
            return False

    def _handle_attack(self, action: AttackAction) -> bool:
        player = self.state.get_active_player()
        
        # 1. Find Attacker
        attacker = None
        if player.leader and player.leader.instance_id == action.attacker_instance_id:
            attacker = player.leader
        else:
            for char in player.field.character_area:
                if char.instance_id == action.attacker_instance_id:
                    attacker = char
                    break
        
        if not attacker:
            return False
            
        # 2. Rest Attacker
        attacker.is_rested = True
        
        # 3. Resolve Battle (Simplified: Just log it)
        # In a real game, steps are: Block -> Counter -> Damage Calculation
        # For now, we assume successful attack for simulation flow
        print(f"    [Engine] {attacker.instance_id} attacks {action.target_instance_id}!")
        
        return True

    def _perform_refresh_phase(self):
        """
        Set all cards to active, return Don.
        """
        player = self.state.get_active_player()
        # Unrest all characters
        for char in player.field.character_area:
            char.is_rested = False
        
        # Unrest Don (TODO)
        pass

    def get_valid_actions(self) -> List[GameAction]:
        """
        Returns a list of all valid actions for the active player.
        """
        actions: List[GameAction] = []
        player = self.state.get_active_player()
        
        # Always allow Ending Phase
        actions.append(EndTurnAction(player_id=player.id, action_type='END_PHASE'))
        
        if self.state.current_phase == 'MAIN_PHASE':
            # 1. Play Cards from Hand
            # Simplified: Check if cost <= active don (Assuming infinite don for now or 10)
            # Todo: Implement real Don checks
            for i, card in enumerate(player.hand):
                # Check target limits etc (Simplified)
                if card.type == 'CHARACTER':
                    if len(player.field.character_area) < 5:
                        actions.append(PlayCardAction(
                            player_id=player.id, 
                            action_type='PLAY_CARD', 
                            card_hand_index=i
                        ))
            
            # 2. Attack (Simplified)
            # Can attack with Active Characters/Leader
            # Targets: Opponent Leader or Rested Characters
            opponent = self.state.get_opponent(player.id)
            
            # Attacker: Leader
            if not player.leader.is_rested:
               # Target: Opponent Leader
               if opponent.leader:
                   actions.append(AttackAction(
                       player_id=player.id,
                       action_type='ATTACK',
                       attacker_instance_id=player.leader.instance_id,
                       target_instance_id=opponent.leader.instance_id
                   ))

            # Attacker: Characters
            for char in player.field.character_area:
                if not char.is_rested:
                     if opponent.leader:
                        actions.append(AttackAction(
                            player_id=player.id,
                            action_type='ATTACK',
                            attacker_instance_id=char.instance_id,
                            target_instance_id=opponent.leader.instance_id
                        ))
        
        return actions
