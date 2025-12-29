import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.core.game import Game
from engine.models.player import Player
from engine.models.card import Card, CardInstance
from engine.core.actions import AttackAction, BlockAction, CounterAction, ResolveBattleAction

class TestComplexBattle(unittest.TestCase):
    def setUp(self):
        self.p1 = Player(id="p1", name="Player 1")
        self.p2 = Player(id="p2", name="Player 2")
        self.game = Game(self.p1, self.p2)
        
        # Populate decks to prevent empty life issue
        dummy_card = Card(id="C1", name="Dummy", type="CHARACTER", power=1000, counter=1000)
        self.p1.deck = [dummy_card] * 10
        self.p2.deck = [dummy_card] * 10
        
        self.game.start_game()
        self.game.state.active_player_id = "p1"
        
        # Setup Field
        self.p1_leader = CardInstance(card_id="L1", instance_id="p1_leader", owner_id="p1", current_power=5000)
        self.p1.leader = self.p1_leader
        
        self.p2_leader = CardInstance(card_id="L2", instance_id="p2_leader", owner_id="p2", current_power=5000)
        self.p2.leader = self.p2_leader
        
        # Add a Blocker for P2
        self.blocker = CardInstance(card_id="B1", instance_id="p2_blocker", owner_id="p2", current_power=1000)
        self.blocker.granted_keywords.append("BLOCKER") # Manually grant keyword
        self.p2.field.add_character(self.blocker)

    def test_blocker_intercept(self):
        """Test Attack -> Block -> Blocker dies -> Original Target safe"""
        
        # 1. Attack P1 -> P2 Leader
        self.game.process_action(AttackAction(
            player_id="p1", 
            action_type="ATTACK",
            attacker_instance_id="p1_leader",
            target_instance_id="p2_leader"
        ))
        
        battle = self.game.state.current_battle
        self.assertEqual(battle.target_instance_id, "p2_leader")
        
        # 2. Block with p2_blocker
        self.game.process_action(BlockAction(
            player_id="p2",
            action_type="BLOCK",
            blocker_instance_id="p2_blocker"
        ))
        
        # Check redirection
        self.assertEqual(battle.target_instance_id, "p2_blocker")
        self.assertEqual(battle.current_step, "COUNTER")
        
        # 3. Resolve (No Counter)
        self.game.process_action(ResolveBattleAction(player_id="p2", action_type="RESOLVE_BATTLE"))
        
        # Result: Blocker dies (1000 vs 5000), Leader safe (Life 5)
        self.assertEqual(len(self.p2.field.character_area), 0) # Blocker removed
        self.assertEqual(len(self.p2.life), 5) # Leader took no damage

    def test_counter_defense(self):
        """Test Attack -> Counter (+1000) -> Attack Fails"""
        # P1 Attacks P2 Leader (5000 vs 5000)
        self.game.process_action(AttackAction(
            player_id="p1", 
            action_type="ATTACK",
            attacker_instance_id="p1_leader",
            target_instance_id="p2_leader"
        ))
        
        battle = self.game.state.current_battle
        
        # Block Step: Skip
        self.game.process_action(ResolveBattleAction(player_id="p2", action_type="RESOLVE_BATTLE"))
        
        # Counter Step: Use Counter (+1000)
        # P2 has dummy cards with 1000 counter in hand (index 0)
        self.game.process_action(CounterAction(
            player_id="p2",
            action_type="COUNTER",
            card_hand_index=0
        ))
        
        # Resolve manually (In real game, player might pass or play more counters, 
        # but here we trigger resolution or check if CounterAction triggered it?
        # My implementation of _handle_counter returns True but doesn't auto-advance yet unless we add logic.
        # Let's verify State is still COUNTER or check logic.
        # _handle_counter DOES NOT call _resolve_battle. We need to explicitly pass (Resolve) to finish.
        
        self.game.process_action(ResolveBattleAction(player_id="p2", action_type="RESOLVE_BATTLE"))
        
        # Result: Attack (5000) < Target (6000). Attack Fails.
        self.assertEqual(len(self.p2.life), 5) # No damage taken


if __name__ == '__main__':
    unittest.main()
