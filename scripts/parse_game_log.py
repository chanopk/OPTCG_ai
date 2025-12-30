
import re

def parse_log(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    current_turn = "0"
    p1_moves = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        # Turn Header
        if line.startswith("[Turn"):
            match = re.search(r"\[Turn (\d+)\]", line)
            if match:
                current_turn = match.group(1)
        
        # Action Line
        if line.startswith("Action:"):
            # Parse dict-like string
            # Action: player_id='p1' action_type='...' ...
            if "player_id='p1'" in line:
                # Extract Action Type
                type_match = re.search(r"action_type='([^']+)'", line)
                action_type = type_match.group(1) if type_match else "UNKNOWN"
                
                details = ""
                # Details for Attack
                if action_type == 'ATTACK':
                    atk_match = re.search(r"attacker_instance_id='([^']+)'", line)
                    tgt_match = re.search(r"target_instance_id='([^']+)'", line)
                    attacker = atk_match.group(1) if atk_match else "?"
                    target = tgt_match.group(1) if tgt_match else "?"
                    details = f"{attacker} -> {target}"
                
                # Details for Play Card
                if action_type == 'PLAY_CARD':
                    card_match = re.search(r"card_hand_index=(\d+)", line)
                    idx = card_match.group(1) if card_match else "?"
                    details = f"Hand Index {idx}"
                
                # Check next line for Engine result (e.g. Battle Resolve)
                outcome = ""
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line.startswith("[Engine]"):
                        outcome = next_line
                    elif next_line.startswith("[Battle]"): # Immediate result
                        outcome = next_line
                
                p1_moves.append({
                    "turn": current_turn,
                    "action": action_type,
                    "details": details,
                    "outcome": outcome
                })

    # Formatting Output
    print(f"Summary of Player 1 (Luffy) Moves:")
    current_t = -1
    for move in p1_moves:
        if move['turn'] != current_t:
            print(f"\n--- Turn {move['turn']} ---")
            current_t = move['turn']
        
        print(f"[{move['action']}] {move['details']}")
        if move['outcome']:
            print(f"  > {move['outcome']}")

if __name__ == "__main__":
    parse_log("game_log.txt")
