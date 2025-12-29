import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.core.game import Game, GameState, Player
from engine.core.effect_manager import EffectManager
from engine.models.effect import Effect, EffectType
from engine.models.card import Card, CardInstance
from engine.models.field import FieldArea

class TestAdvancedEffects(unittest.TestCase):
    def setUp(self):
        # Setup basic game state
        self.p1 = Player(id="p1", name="Player 1")
        self.p2 = Player(id="p2", name="Player 2")
        self.state = GameState(game_id="test_game", players={"p1": self.p1, "p2": self.p2}, active_player_id="p1")
        self.manager = EffectManager(self.state)
        
        # Helper to simplify card instance creation
        self.dummy_card = Card(id="test01", name="Test Card", type="CHARACTER")
        
    def test_draw_card(self):
        # Setup deck
        self.p1.deck = [self.dummy_card, self.dummy_card]
        
        effect = Effect(type=EffectType.DRAW_CARD, action_code=EffectType.DRAW_CARD, action_value=2)
        success = self.manager.resolve_effect(effect, "source")
        
        self.assertTrue(success)
        self.assertEqual(len(self.p1.hand), 2)
        self.assertEqual(len(self.p1.deck), 0)
        
    def test_buff_power(self):
        # Setup char on field
        char = CardInstance(card_id="test01", instance_id="char1", owner_id="p1")
        self.p1.field.add_character(char)
        
        effect = Effect(type=EffectType.BUFF_POWER, action_code=EffectType.BUFF_POWER, action_power=2000)
        success = self.manager.resolve_effect(effect, "source", target_id="char1")
        
        self.assertTrue(success)
        self.assertEqual(char.power_modifier, 2000)
        
    def test_cost_change(self):
        char = CardInstance(card_id="test01", instance_id="char2", owner_id="p2")
        self.p2.field.add_character(char)
        
        # Give -2 Cost
        effect = Effect(type=EffectType.COST_CHANGE, action_code=EffectType.COST_CHANGE, action_value=-2)
        success = self.manager.resolve_effect(effect, "source", target_id="char2")
        
        self.assertTrue(success)
        self.assertEqual(char.cost_modifier, -2)
        
    def test_grant_keywords(self):
        char = CardInstance(card_id="test01", instance_id="rusher", owner_id="p1")
        self.p1.field.add_character(char)
        
        # Rush
        effect = Effect(type=EffectType.RUSH, action_code=EffectType.RUSH)
        success = self.manager.resolve_effect(effect, "source", target_id="rusher")
        
        self.assertTrue(success)
        self.assertIn("RUSH", char.granted_keywords)
        
        # Blocker
        effect2 = Effect(type=EffectType.BLOCKER, action_code=EffectType.BLOCKER)
        success2 = self.manager.resolve_effect(effect2, "source", target_id="rusher")
        self.assertIn("BLOCKER", char.granted_keywords)

    def test_ko_character(self):
        char = CardInstance(card_id="test01", instance_id="victim", owner_id="p2")
        self.p2.field.add_character(char)
        
        effect = Effect(type=EffectType.KO_CHARACTER, action_code=EffectType.KO_CHARACTER)
        success = self.manager.resolve_effect(effect, "source", target_id="victim")
        
        self.assertTrue(success)
        self.assertEqual(len(self.p2.field.character_area), 0)

if __name__ == '__main__':
    unittest.main()
