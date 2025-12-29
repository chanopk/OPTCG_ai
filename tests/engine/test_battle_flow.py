import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.core.game import Game
from engine.models.player import Player
from engine.models.card import Card, CardInstance
from engine.core.actions import AttackAction, BlockAction, ResolveBattleAction

class TestBattleFlow(unittest.TestCase):
    def setUp(self):
        self.p1 = Player(id="p1", name="Player 1")
        self.p2 = Player(id="p2", name="Player 2")
        self.game = Game(self.p1, self.p2)
        self.game.state.active_player_id = "p1"
        self.game.start_game()
        
        # Setup Field
        # P1 has Leader and 1 Attacker
        self.p1_leader = CardInstance(card_id="L1", instance_id="p1_leader", owner_id="p1", current_power=5000)
        self.p1.leader = self.p1_leader
        
        # P2 has Leader and 1 Blocker
        self.p2_leader = CardInstance(card_id="L2", instance_id="p2_leader", owner_id="p2", current_power=5000)
        self.p2.leader = self.p2_leader
        
        self.blocker_card = CardInstance(card_id="B1", instance_id="p2_blocker", owner_id="p2", current_power=1000)
        # Manually verify blocker logic usually requires checking effects or traits, 
        # but for now we test the FLOW actions.
        self.p2.field.add_character(self.blocker_card)

    def test_basic_attack_resolve(self):
        """Test simple Attack -> No Block -> Resolve damage"""
        
        # 1. Attack Declaration (P1 Leader -> P2 Leader)
        attack_action = AttackAction(
            player_id="p1", 
            action_type="ATTACK",
            attacker_instance_id="p1_leader",
            target_instance_id="p2_leader"
        )
        
        success = self.game.process_action(attack_action)
        self.assertTrue(success)
        self.assertIsNotNone(self.game.state.current_battle)
        self.assertEqual(self.game.state.current_battle.current_step, "BLOCK")
        
        # 2. Block Step (P2 passes)
        # Opponent (P2) must act now
        pass_block = ResolveBattleAction(player_id="p2", action_type="RESOLVE_BATTLE") # Using Resolve as "Pass" per current simplified logic
        
        # In game.py logic:
        # if battle.current_step == 'BLOCK': actions.append(ResolveBattleAction(...))
        # Wait, _handle_block logic in game.py is TODO. 
        # But get_valid_actions returns ResolveBattleAction for "Pass".
        # Let's check process_action for RESOLVE_BATTLE.
        
        success = self.game.process_action(pass_block)
        
        # Based on game.py: _resolve_battle is called immediately if action is RESOLVE_BATTLE
        # But wait, logic might skip COUNTER step?
        # get_valid_actions says:
        # if BLOCK step -> return Resolve (Pass)
        # process_action -> RESOLVE_BATTLE -> _resolve_battle()
        # So it skips Counter step in current implementation? 
        # Yes, line 214 in game.py (Counter logic) just calls resolve.
        # And get_valid_actions for Block step returns ResolveBattleAction which calls _resolve_battle directly?
        # Actually line 297: actions.append(ResolveBattleAction(...))
        
        self.assertTrue(success)
        self.assertIsNone(self.game.state.current_battle) # Battle should end
        
        # Check damage (5000 vs 5000 -> Hit -> Life lost)
        # Initial life is 5. Should be 4.
        self.assertEqual(len(self.p2.life), 4)

if __name__ == '__main__':
    unittest.main()
