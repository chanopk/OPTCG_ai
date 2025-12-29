import re
from typing import List, Optional
from engine.models.effect import Effect, EffectType

class EffectParser:
    """
    Parses raw card text into structured Effect objects.
    """
    
    def parse_effects(self, effect_text: str) -> List[Effect]:
        """
        Main entry point to parse a full effect text block.
        Splits by keywords like [On Play], [When Attacking], etc.
        """
        if not effect_text:
            return []
            
        effects = []
        
        # Normalize
        text = effect_text.replace("\r\n", " ").replace("<br>", " ")

        # --- Extract Global Costs/Conditions (Naive) ---
        # "DON!! -X" -> Cost
        # "DON!! xX" -> Condition
        # These usually apply to the ACTIVATE effects they are adjacent to, 
        # but for now, if found at start of text, we might apply to all? 
        # Better: _parse_single_effect should check for them in the specific effect chunk.
        
        # Check for On Play
        if "[On Play]" in text:
            # Extract content after [On Play] until next tag or end
            content = self._extract_content(text, "[On Play]")
            effect = self._parse_single_effect(EffectType.ON_PLAY, content)
            if effect:
                effects.append(effect)

        # Check for When Attacking
        if "[When Attacking]" in text:
            content = self._extract_content(text, "[When Attacking]")
            effect = self._parse_single_effect(EffectType.WHEN_ATTACKING, content)
            if effect:
                effects.append(effect)
                
        # Check for Activate: Main
        if "[Activate: Main]" in text or "[Activate:Main]" in text:
             # Normalize tag first?
             tag = "[Activate:Main]" if "[Activate:Main]" in text else "[Activate: Main]"
             content = self._extract_content(text, tag)
             effect = self._parse_single_effect(EffectType.ACTIVATE_MAIN, content)
             if effect:
                 effects.append(effect)

        # Check for Blocker
        if "[Blocker]" in text:
            effects.append(Effect(type=EffectType.BLOCKER, action_code=EffectType.BLOCKER, description="[Blocker]"))
            
        if "[Rush]" in text:
            effects.append(Effect(type=EffectType.RUSH, action_code=EffectType.RUSH, description="[Rush]"))
            
        if "[Banish]" in text:
            effects.append(Effect(type=EffectType.BANISH, action_code=EffectType.BANISH, description="[Banish]"))
            
        if "[Double Attack]" in text:
            effects.append(Effect(type=EffectType.DOUBLE_ATTACK, action_code=EffectType.DOUBLE_ATTACK, description="[Double Attack]"))

        # --- General Text Parsing (regex) ---
        text_lower = text.lower()
        
        # Check for Draw
        if "draw" in text_lower:
            draw_match = re.search(r"draw (\d+) cards?", text_lower)
            if draw_match:
                count = int(draw_match.group(1))
                effects.append(Effect(type=EffectType.DRAW_CARD, action_code=EffectType.DRAW_CARD, value=count, description=f"Draw {count} cards"))

        # Check for Trash
        if "trash" in text_lower:
            # "trash x cards from your hand"
            trash_match = re.search(r"trash (\d+) cards? from your hand", text_lower)
            if trash_match:
                count = int(trash_match.group(1))
                effects.append(Effect(type=EffectType.TRASH_CARD, action_code=EffectType.TRASH_CARD, value=count, description=f"Trash {count} cards from hand"))

        # Check for Return to Hand
        if "return" in text_lower and "hand" in text_lower:
            return_match = re.search(r"return up to (\d+) .*? to the owner's hand", text_lower)
            if return_match:
                count = int(return_match.group(1))
                effects.append(Effect(type=EffectType.RETURN_TO_HAND, action_code=EffectType.RETURN_TO_HAND, value=count, description="Return to hand"))
        
        # Check for Return to Bottom of Deck
        if "bottom" in text_lower and "deck" in text_lower and ("place" in text_lower or "return" in text_lower):
             # "Place up to 1 ... at the bottom of the owner's deck"
             deck_match = re.search(r"(?:place|return) up to (\d+) .*? (?:at|to) the bottom of the owner's deck", text_lower)
             if deck_match:
                 count = int(deck_match.group(1))
                 effects.append(Effect(type=EffectType.RETURN_TO_BOTTOM_DECK, action_code=EffectType.RETURN_TO_BOTTOM_DECK, value=count, description="Return to bottom deck"))

        # Check for Cost Change (Give -X cost)
        if "cost" in text_lower and "give" in text_lower:
             cost_match = re.search(r"give .*? (-?\d+) cost", text_lower)
             if cost_match:
                 val = int(cost_match.group(1))
                 effects.append(Effect(type=EffectType.COST_CHANGE, action_code=EffectType.COST_CHANGE, value=val, description=f"Give {val} cost"))

        # Check for Trigger
        if "[Trigger]" in text:
            content = self._extract_content(text, "[Trigger]")
            effect = self._parse_single_effect(EffectType.TRIGGER, content)
            if effect:
                effects.append(effect)
                
        return effects

    def _extract_content(self, text: str, tag: str) -> str:
        """
        Extracts text immediately following a tag, up to the next tag or end of string.
        """
        start_idx = text.find(tag)
        if start_idx == -1:
            return ""
        
        start_content = start_idx + len(tag)
        sub_text = text[start_content:].strip()
        
        # Find next tag to stop
        # Potential tags: [On Play], [When Attacking], [Your Turn], [Blocker], etc.
        # Simple heuristic: Look for next '[' that starts a known tag? 
        # For now, let's just take the rest of the string or split by common delimiters if needed.
        # But often multiple effects are separated clearly.
        # Let's assume one main effect per tag for this POC or take until end of sentence if robust.
        
        return sub_text

    def _parse_single_effect(self, effect_type: EffectType, content: str) -> Optional[Effect]:
        """
        Analyzes the content text to determine the specific action (KO, Buff, etc.)
        """
        # Default fallback
        action_code = None
        action_power = 0
        target_filter = None
        condition_don = 0
        condition_cost = 0
        
        content_lower = content.lower()
        
        # --- Extract Costs ---
        # DON!! -X (Return X Don to deck)
        don_minus_match = re.search(r"don!! -(\d+)", content_lower)
        if don_minus_match:
            condition_cost = int(don_minus_match.group(1))
            
        # DON!! xX (Need X Don attached)
        # Usually this is outside the Effect bracket in the card text, but sometimes inside?
        # Example: [DON!! x2] [When Attacking] ...
        # If it's passed here, 'content' is what's AFTER the tag. 
        # If [DON!! x2] was BEFORE the tag, we missed it in the current naive structure.
        # But often it appears like: "[Activate: Main] DON!! -1: ..." 
        
        # If the content starts with "DON!! -X:", it's definitely a cost for this effect.
        
        # --- Heuristics ---
        
        # 1. BUFF POWER
        # "Give this Character +1000 power" / "Gains +2000 power"
        if "+" in content and "power" in content_lower:
            action_code = EffectType.BUFF_POWER
            # Extract number
            match = re.search(r'\+(\d+)', content)
            if match:
                action_power = int(match.group(1))
            
            # Target
            if "this character" in content_lower:
                target_filter = "self"
            elif "leader" in content_lower:
                target_filter = "leader"
            elif "up to 1 of your opponent's characters" in content_lower:  
                 # Actually this is usually DEBUFF, e.g. -2000
                 pass
                 
            # Check for Debuff (Negative power)
            if "-" in content:
                 match_neg = re.search(r'-(\d+)', content)
                 if match_neg:
                     action_power = -int(match_neg.group(1))
                     
        # 2. KO CHARACTER
        # "K.O. up to 1 of your opponent's Characters with a cost of 3 or less"
        elif "k.o." in content_lower:
            action_code = EffectType.KO_CHARACTER
            # Extract Cost Constraint
            cost_match = re.search(r'cost of (\d+) or less', content_lower)
            if cost_match:
                cost_val = int(cost_match.group(1))
                target_filter = f"opponent|character|cost<={cost_val}"
            else:
                target_filter = "opponent|character" # Generic KO? Unlikely but fallback

        # 3. DON MANIPULATION (Simple)
        # "Add up to 1 DON!! card from your DON!! deck"
        elif "add" in content_lower and "don!!" in content_lower:
             pass # TODO: Implement Ramp effect
             
        if action_code:
            return Effect(
                type=effect_type,
                action_code=action_code,
                action_power=action_power,
                condition_cost=condition_cost,
                condition_don=condition_don,
                target_filter=target_filter,
                description=content.strip()[:50] + "..." # truncated
            )
            
        return None
