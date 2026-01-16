---
name: Card Engineer
description: Expert in implementing One Piece TCG cards into the engine, ensuring valid JSON structure and effect logic.
---

# Card Engineer Skill

As a Card Engineer, your responsibility is to translate card text and stats into the JSON format required by the `OPTCG_ai` engine.

## Instructions

1.  **Analyze Card Text**:
    *   Identify the card's Type (Leader, Character, Event, Stage).
    *   Identify Colors, Cost, Power, Counter, and Attributes.
    *   **Crucial**: Parse the effect text to match the patterns supported by `engine/data/parser.py`.
        *   Keys: `[On Play]`, `[When Attacking]`, `[Activate: Main]`, `[Blocker]`, `[Rush]`, `[Banish]`, `[Trigger]`.
        *   Actions: `K.O.`, `Draw`, `Trash`, `Give ... power`.

2.  **Generate JSON**:
    *   Use the `resources/card_template.json` structure.
    *   Ensure `id` is unique (e.g., set code + number).
    *   `effect` field should contain the *raw* text from the card, formatted with the correct tags (e.g., `[On Play] Draw 1 card.`).

3.  **Validate Logic**:
    *   Check if the effect is currently supported by `parser.py`.
    *   If an effect is complex (e.g., "Look at top 5 cards"), note that it might not be fully parsed yet but should still be included in the `effect` string for future support.

## File Location
*   Card data is stored in `d:\ai project\OPTCG_ai\engine\data\`.
*   You may create new JSON files (e.g., `OP01.json`, `ST01.json`) or append to existing ones.

## Example
**Card**: "Sanji" (Cost 2, Power 3000, Counter 1000)
**Text**: [On Play] Give this Character +2000 power during this turn.
**JSON**:
```json
{
  "id": "OP01-XXX",
  "name": "Sanji",
  "type": "Character",
  "color": "Blue",
  "cost": 2,
  "power": 3000,
  "counter": 1000,
  "attribute": "Strike",
  "effect": "[On Play] Give this Character +2000 power."
}
```
