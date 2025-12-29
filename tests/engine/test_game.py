import pytest
from engine.core.game import Game
from engine.models.player import Player
from engine.models.card import Card
from engine.core.actions import PlayCardAction, EndTurnAction

def test_initialization():
    p1 = Player(id="p1", name="Luffy")
    p2 = Player(id="p2", name="Kaido")
    game = Game(p1, p2)
    
    assert game.state.active_player_id == "p1"
    assert game.state.turn_count == 1
    assert game.state.current_phase == "REFRESH_PHASE"

def test_phase_transition():
    p1 = Player(id="p1", name="Luffy")
    p2 = Player(id="p2", name="Kaido")
    game = Game(p1, p2)
    
    # REFRESH -> DRAW
    game._handle_end_phase() 
    assert game.state.current_phase == "DRAW_PHASE"
    
    # DRAW -> DON
    game._handle_end_phase()
    assert game.state.current_phase == "DON_PHASE"
    
    # DON -> MAIN
    game._handle_end_phase()
    assert game.state.current_phase == "MAIN_PHASE"
    
    # MAIN -> END
    game._handle_end_phase()
    assert game.state.current_phase == "END_PHASE"
    
    # END -> REFRESH (Next Turn, Switch Player)
    game._handle_end_phase()
    assert game.state.current_phase == "REFRESH_PHASE"
    assert game.state.active_player_id == "p2"
    assert game.state.turn_count == 2

def test_play_card():
    p1 = Player(id="p1", name="Luffy")
    card = Card(id="OP01-001", name="Zoro", type="CHARACTER", cost=3, power=5000)
    p1.hand.append(card)
    
    p2 = Player(id="p2", name="Kaido")
    game = Game(p1, p2)
    
    # Fast forward to MAIN phase
    game.state.current_phase = "MAIN_PHASE"
    
    # Action: Play Card
    action = PlayCardAction(player_id="p1", card_hand_index=0)
    success = game.process_action(action)
    
    assert success is True
    assert len(p1.hand) == 0
    assert len(p1.field.character_area) == 1
    assert p1.field.character_area[0].card_id == "OP01-001"
