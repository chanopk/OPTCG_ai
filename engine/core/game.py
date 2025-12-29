from typing import List, Optional
import random
from engine.state import GameState, PhaseType
from engine.core.phases import PhaseManager, Phase
from engine.core.actions import GameAction, PlayCardAction, AttackAction, EndTurnAction, BlockAction, CounterAction, ResolveBattleAction
from engine.models.player import Player
from engine.models.card import CardInstance
from engine.core.battle import BattlePhase
from engine.core.effect_manager import EffectManager

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
        self.effect_manager = EffectManager(self.state)
        
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
        expected_player = self.state.active_player_id
        
        # Exception: Battle Steps (Block/Counter)
        if self.state.current_battle:
            battle = self.state.current_battle
            if battle.current_step in ['BLOCK', 'COUNTER']:
                expected_player = self.state.get_opponent(battle.attacker_id).id
                
        if action.player_id != expected_player:
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
        
        elif action.action_type == 'BLOCK':
            # TODO: Implement Block Logic
            return self._handle_block(action)
            
        elif action.action_type == 'COUNTER':
             # TODO: Implement Counter Logic
             return self._handle_counter(action)
             
        elif action.action_type == 'RESOLVE_BATTLE':
             # If in BLOCK step, passing means going to COUNTER step
             if self.state.current_battle and self.state.current_battle.current_step == 'BLOCK':
                 self.state.current_battle.current_step = 'COUNTER'
                 return True
             # If in COUNTER step, passing means finishing battle
             return self._resolve_battle()
                
        return False
        
    def _handle_end_phase(self) -> bool:
        if self.state.current_battle:
            return False # Cannot end phase during battle
            
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
        if self.state.current_battle:
             return False # Cannot play character during battle
             
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
            # CHECK ON PLAY EFFECTS
            # Simplified: Check if card has ON_PLAY effect in list
            # We need to lookup the original Card definition for effects
            # ideally CardInstance should trigger this via ID lookup
            # For now, let's assume we can get effects from the card object we popped
            for effect in card.effect_list:
                if effect.type == 'ON_PLAY':
                     print(f"    [Effect] Triggering ON_PLAY for {card.name}")
                     self.effect_manager.resolve_effect(effect, instance.instance_id)

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
        
        # 3. Start Battle Phase (Transient State)
        self.state.current_battle = BattlePhase(
            attacker_id=player.id,
            attacker_instance_id=action.attacker_instance_id,
            target_instance_id=action.target_instance_id,
            current_step="BLOCK", # Next step is BLOCK
            attacker_power=attacker.total_power
        )
        
        # Determine Target Power for snapshot
        opponent = self.state.get_opponent(player.id)
        target = None
        if opponent.leader and opponent.leader.instance_id == action.target_instance_id:
            target = opponent.leader
        else:
             for char in opponent.field.character_area:
                if char.instance_id == action.target_instance_id:
                    target = char
                    break
        
        if target:
            self.state.current_battle.target_power = target.total_power

        print(f"    [Engine] {attacker.instance_id} attacks {action.target_instance_id}! (Battle Started)")
        return True

    def _handle_block(self, action: BlockAction) -> bool:
        battle = self.state.current_battle
        if not battle: return False
        
        # Validate Blocker
        player = self.state.players.get(action.player_id)
        blocker = None
        for char in player.field.character_area:
            if char.instance_id == action.blocker_instance_id:
                blocker = char
                break
        
        if not blocker: return False
        if blocker.is_rested: return False # Cannot block if rested
        
        # Check if blocker has BLOCKER trait (Need to check Card traits or keywords)
        # Simplified: Check granted_keywords
        if "BLOCKER" not in blocker.granted_keywords and "BLOCKER" not in [t.upper() for t in blocker.granted_keywords]:
             # Also check generic traits if we parsed it?
             # EffectManager grants BLOCKER keyword.
             # If parsed from JSON but not played via EffectManager (e.g. from test setup), we might miss it.
             # For now, rely on granted_keywords.
             pass 

        if action.action_type == 'BLOCK':
             battle.blocker_instance_id = action.blocker_instance_id
             # Change target to blocker
             battle.target_instance_id = action.blocker_instance_id
             battle.target_power = blocker.total_power
             
             battle.current_step = "COUNTER"
             print(f"    [Battle] Blocked by {action.blocker_instance_id}! New Target: {action.blocker_instance_id}")
             
             # Rest the blocker
             blocker.is_rested = True
             return True
        return False
        
    def _handle_counter(self, action: CounterAction) -> bool:
        battle = self.state.current_battle
        if not battle: return False
        
        # Validate Counter Card (simplified: assumed from hand)
        player = self.state.players.get(action.player_id)
        if action.card_hand_index >= len(player.hand): return False
        
        card = player.hand.pop(action.card_hand_index)
        # Use card counter power (default 1000 if not set)
        counter_power = card.counter
        
        # Apply to current target (could be Leader or Blocker)
        target = None
        # Check Leader
        target_owner = self.state.players.get(battle.target_instance_id.split('_')[0]) # HACK to get owner?
        # Better: Search current target instance
        if battle.target_instance_id == player.leader.instance_id:
            target = player.leader
        else:
            for char in player.field.character_area:
                if char.instance_id == battle.target_instance_id:
                    target = char
                    break
        
        if target:
            target.power_modifier += counter_power
            battle.target_power = target.total_power # Update snapshot
            print(f"    [Battle] Counter by {card.name} (+{counter_power}) -> Target Power: {battle.target_power}")
            player.trash.append(card)
            return True
            
        return False

    def _resolve_battle(self) -> bool:
        battle = self.state.current_battle
        if not battle: return False
        
        # Compare Power
        # Simplified: Attacker vs Target (Ignoring Blocker power calc for now)
        attacker_power = battle.attacker_power
        target_power = battle.target_power
        
        print(f"    [Battle] Resolve: {attacker_power} vs {target_power}")
        
        if attacker_power >= target_power:
            # Hit!
            # If Target is Leader -> Take Life
            opponent = self.state.get_opponent(battle.attacker_id)
            if opponent.leader and opponent.leader.instance_id == battle.target_instance_id:
                if opponent.life:
                    lost_life = opponent.life.pop(0)
                    opponent.hand.append(lost_life) # Life to Hand
                    print(f"    [Battle] Hit Leader! Life -> Hand: {lost_life.name}")
                    if not opponent.life:
                         # Check win condition? (Usually only when taking hit at 0 life)
                         # Assuming hitting at 0 life = Win
                         pass
                else:
                    # No life left
                    self.state.winner_id = battle.attacker_id
                    print(f"    [Battle] WINNER: {battle.attacker_id}")

            # If Target is Character -> KO
            else:
                 removed = opponent.field.remove_character(battle.target_instance_id)
                 if removed:
                     print(f"    [Battle] KO Character: {removed.instance_id}")

        else:
            print("    [Battle] Attack Failed (Not enough power)")

        # End Battle
        self.state.current_battle = None
        return True

    def _perform_refresh_phase(self):
        """
        Set all cards to active, return Don.
        """
        player = self.state.get_active_player()
        # Unrest all characters
        if player.leader:
             player.leader.is_rested = False
             
        for char in player.field.character_area:
            char.is_rested = False
        
        # Unrest Don (TODO)
        pass

    def get_valid_actions(self) -> List[GameAction]:
        """
        Returns a list of all valid actions for the active player.
        """
        actions: List[GameAction] = []
        
        # If Battle is active, restrict actions based on Step
        if self.state.current_battle:
            battle = self.state.current_battle
            # Who is acting?
            # BLOCK/COUNTER are Opponent's actions
            opponent_id = self.state.get_opponent(battle.attacker_id).id
            
            # Who is acting?
            # BLOCK/COUNTER are Opponent's actions
            opponent_id = self.state.get_opponent(battle.attacker_id).id
            
            # If we are in BLOCK step
            if battle.current_step == 'BLOCK':
                # Add 'No Block' (Pass) which moves to Counter/Damage
                # In real game, this is skipping block.
                # We reuse ResolveBattleAction for "Skip/Done" signal for now or define a new "SkipBlockAction"
                # To keep it simple, let's use RESOLVE_BATTLE as "Pass priority"
                actions.append(ResolveBattleAction(player_id=opponent_id, action_type='RESOLVE_BATTLE'))
                
                # Check for Blockers
                opponent = self.state.get_opponent(battle.attacker_id)
                for char in opponent.field.character_area:
                    # Valid Blocker: Not Rested + Has BLOCKER keyword
                    if not char.is_rested and "BLOCKER" in char.granted_keywords:
                         actions.append(BlockAction(
                             player_id=opponent.id,
                             action_type='BLOCK',
                             blocker_instance_id=char.instance_id
                         ))
            
            elif battle.current_step == 'COUNTER':
                 # Add 'No Counter' (Pass)
                 actions.append(ResolveBattleAction(player_id=opponent_id, action_type='RESOLVE_BATTLE'))
            
            else:
                 # Should not happen if auto-transitioned, but safely return resolve
                 actions.append(ResolveBattleAction(player_id=battle.attacker_id, action_type='RESOLVE_BATTLE'))
                 
            return actions

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
            if player.leader and not player.leader.is_rested:
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
