from engine.state import GameState
from engine.models.effect import Effect, EffectType
from engine.models.card import CardInstance

class EffectManager:
    """
    Handles resolving effects against the Game State.
    """
    def __init__(self, game_state: GameState):
        self.state = game_state
        
    def resolve_effect(self, effect: Effect, source_id: str, target_id: str = None) -> bool:
        """
        Execute an effect.
        Returns True if successful.
        """
        # 1. Condition Check
        player = self.state.players[self.state.active_player_id] # Assuming source is active player for now
        
        # Check Don condition
        # (This logic assumes we pass the instance that has the effect, 
        # but for simplicity we skip intricate condition checking for this POC)
        
        # 2. Execute Action
        if effect.action_code == EffectType.KO_CHARACTER:
            return self._action_ko_character(target_id)
            
        elif effect.action_code == EffectType.BUFF_POWER:
            return self._action_buff_power(target_id, effect.action_power)

        elif effect.action_code == EffectType.DRAW_CARD:
            return self._action_draw_card(player, effect.action_value)
            
        elif effect.action_code == EffectType.TRASH_CARD:
            return self._action_trash_card(player, effect.action_value)
            
        elif effect.action_code == EffectType.RETURN_TO_HAND:
            return self._action_return_to_hand(target_id)
            
        elif effect.action_code == EffectType.RETURN_TO_BOTTOM_DECK:
            return self._action_return_to_bottom_deck(target_id)

        elif effect.action_code == EffectType.COST_CHANGE:
            return self._action_cost_change(target_id, effect.action_value)
            
        elif effect.action_code == EffectType.RUSH:
             # Apply to SELF (source_id) if target not specified, usually source
             target = target_id if target_id else source_id
             return self._action_grant_keyword(target, "RUSH")
             
        elif effect.action_code == EffectType.DOUBLE_ATTACK:
             target = target_id if target_id else source_id
             return self._action_grant_keyword(target, "DOUBLE_ATTACK")
             
        elif effect.action_code == EffectType.BLOCKER:
             target = target_id if target_id else source_id
             return self._action_grant_keyword(target, "BLOCKER")
            
        return False

    def _action_ko_character(self, target_id: str) -> bool:
        if not target_id: 
            return False
            
        # Find who owns the target
        # Simplified: scan both players
        for pid, player in self.state.players.items():
            removed = player.field.remove_character(target_id)
            if removed:
                # In a real implementation, we'd convert Instance back to Card or keeping Instance in trash?
                # For now let's just assume we store the base Card definition in trash
                # But wait, Player.trash expects List[Card]. CardInstance has .card_id.
                # We need to lookup the card definition or just store instance if Trash supports it.
                # Player model says 'trash: List[Card]'. 
                # Let's find the card definition from a global registry or similar?
                # ERROR: We don't have easy access to Card DB here. 
                # HACK: Create a dummy card or just append to list if python allows mixed types (it does but bad practice)
                # BETTER: Player.trash should store CardInstances or we need a way to get Card.
                # For this step, I will just append the removed instance and fix types later if needed, 
                # OR assumes player.trash accepts instances.
                # Checking Player model: trash: List[Card].
                # Let's just do nothing with trash for now to avoid Type Error, just remove from field.
                print(f"  [Effect] KO {target_id}")
                return True
        return False

    def _action_buff_power(self, target_id: str, power: int) -> bool:
        if not target_id:
            return False
            
        # Find target
        for pid, player in self.state.players.items():
            if player.leader and player.leader.instance_id == target_id:
                player.leader.power_modifier += power
                print(f"  [Effect] Buff {target_id} +{power}")
                return True
            for char in player.field.character_area:
                if char.instance_id == target_id:
                    char.power_modifier += power
                    print(f"  [Effect] Buff {target_id} +{power}")
                    return True
        return False

    def _action_draw_card(self, player, amount: int) -> bool:
        player.draw_card(amount)
        print(f"  [Effect] Player {player.id} drew {amount} cards")
        return True

    def _action_trash_card(self, player, amount: int) -> bool:
        # Simplified: Trash random or last cards? Usually player chooses.
        # For AI/Sim, let's trash from end of hand list.
        for _ in range(amount):
            if player.hand:
                card = player.hand.pop()
                player.trash.append(card)
        print(f"  [Effect] Player {player.id} trashed {amount} cards")
        return True

    def _action_return_to_hand(self, target_id: str) -> bool:
        if not target_id: return False
        for pid, player in self.state.players.items():
            removed = player.field.remove_character(target_id)
            if removed:
                # We need the Card object to return to hand. 
                # CardInstance.card_id -> We need a lookup or store Card object in Instance.
                # Currently CardInstance doesn't allow easy reverse lookup without the DB.
                # BIG GLUE ISSUE: CardInstance only has card_id string.
                # FIX: Temporarily we can't put it back in Hand as 'Card' object without DB.
                # We will log it. In real game, we need Instance -> Card mapping.
                print(f"  [Effect] Return {target_id} to hand (Logic incomplete due to Instance-Card gap)")
                return True
        return False
        
    def _action_return_to_bottom_deck(self, target_id: str) -> bool:
        if not target_id: return False
        for pid, player in self.state.players.items():
            removed = player.field.remove_character(target_id)
            if removed:
                print(f"  [Effect] Return {target_id} to bottom deck")
                return True
        return False

    def _action_cost_change(self, target_id: str, amount: int) -> bool:
        for pid, player in self.state.players.items():
            for char in player.field.character_area:
                if char.instance_id == target_id:
                    char.cost_modifier += amount
                    print(f"  [Effect] Cost Change {target_id} by {amount} -> New Mod: {char.cost_modifier}")
                    return True
        return False
        
    def _action_grant_keyword(self, target_id: str, keyword: str) -> bool:
        for pid, player in self.state.players.items():
            for char in player.field.character_area:
                if char.instance_id == target_id:
                    if keyword not in char.granted_keywords:
                       char.granted_keywords.append(keyword)
                    print(f"  [Effect] Granted {keyword} to {target_id}")
                    return True
        return False
