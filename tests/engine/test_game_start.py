import pytest
from engine.core.game import Game
from engine.models.player import Player
from engine.models.card import Card

def test_start_game_initialization():
    # Setup Deck with 50 cards
    dummy_card = Card(id="OP01-001", name="Dummy", type="CHARACTER", cost=1, power=1000)
    deck1 = [dummy_card for _ in range(50)]
    deck2 = [dummy_card for _ in range(50)]
    
    p1 = Player(id="p1", name="Luffy", deck=deck1)
    p2 = Player(id="p2", name="Kaido", deck=deck2)
    
    game = Game(p1, p2)
    game.start_game()
    
    # Check Life (Should be 5)
    assert len(p1.life) == 5
    assert len(p2.life) == 5
    
    # Check Hand (Should be 5)
    assert len(p1.hand) == 5
    assert len(p2.hand) == 5
    
    # Check Deck (Start 50 - 5 Life - 5 Hand = 40)
    assert len(p1.deck) == 40
    assert len(p2.deck) == 40
