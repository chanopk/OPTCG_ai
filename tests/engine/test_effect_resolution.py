import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.core.game import Game
from engine.models.player import Player
from engine.models.card import Card, CardInstance
from engine.models.effect import Effect, EffectType
from engine.core.actions import PlayCardAction

class TestEffectResolution(unittest.TestCase):
    def setUp(self):
        self.p1 = Player(id="p1", name="Player 1")
        self.p2 = Player(id="p2", name="Player 2")
        self.game = Game(self.p1, self.p2)
        self.game.start_game()
        self.game.state.active_player_id = "p1"
        
        # Helper to create card with effect
        self.draw_card_def = Card(
            id="test_draw", 
            name="Nami", 
            type="CHARACTER", 
            power=3000, 
            cost=2,
            effect_list=[
                Effect(type=EffectType.ON_PLAY, action_code=EffectType.DRAW_CARD, action_value=1, description="On Play: Draw 1")
            ]
        )
        
        self.ko_card_def = Card(
            id="test_ko",
            name="Robin",
            type="CHARACTER",
            power=4000,
            cost=3,
            effect_list=[
                # Logic in Game.py might need updating to target something.
                # Currently resolve_effect takes target_id, but PlayCardAction doesn't specify target for OnPlay.
                # EffectManager logic for KO requires target_id.
                # We might need to handle targeting logic later. 
                # For now let's test DRAW which is auto-target (Self/Player).
            ]
        )

    def test_on_play_draw(self):
        """Test that playing a card triggers its On Play Draw effect"""
        # Give P1 the card
        self.p1.hand.insert(0, self.draw_card_def)
        initial_hand_size = len(self.p1.hand)
        # initial_hand_size includes the card we are about to play.
        # So after play (-1) and draw (+1), hand size should be same?
        # Wait, start_game gives 5 cards. +1 insert = 6.
        # Play 1 -> 5. Effect Draw 1 -> 6.
        
        # Deck needs cards
        dummy = Card(id="C1", name="Dummy", type="CHARACTER")
        self.p1.deck = [dummy] * 5
        
        action = PlayCardAction(
            player_id="p1",
            action_type="PLAY_CARD",
            card_hand_index=0
        )
        
        success = self.game.process_action(action)
        self.assertTrue(success)
        
        # Check Hand Size
        # Expected: Starts with 6 (5+1). Plays 1 (-1). Effect Draws 1 (+1). Result: 6.
        self.assertEqual(len(self.p1.hand), initial_hand_size)
        
        # Verify card is on field
        self.assertEqual(len(self.p1.field.character_area), 1)
        self.assertEqual(self.p1.field.character_area[0].card_id, "test_draw")

if __name__ == '__main__':
    unittest.main()
