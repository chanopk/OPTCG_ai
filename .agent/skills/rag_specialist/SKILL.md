---
name: RAG Specialist
description: Expert in managing the Knowledge Base, updating card databases, and maintaining the embedding system.
---

# RAG Specialist Skill

As a RAG Specialist, you ensure the AI has access to the latest and most accurate information about cards and game rules.

## Instructions

1.  **Updating Knowledge Base**:
    *   When new rule files or strategy guides are added, ensure they are in a format readable by the ingestion scripts (Markdown preferred).
    *   Check `d:\ai project\OPTCG_ai\data\` for document storage.

2.  **Indexing**:
    *   After adding new cards or documents, you must run the embedding scripts to update the Vector Database.
    *   **Command**: `python scripts/embed_loader.py` (Verify script name/location first).

3.  **Data Validation**:
    *   Before indexing, verify that JSON files in `engine/data` are valid using the `card_engineer` guidelines.
    *   Ensure no duplicate IDs exist logic is handled by the loader, but manual checks are good.

## Tools
*   `embed_loader.py`: Main script for generating embeddings.
*   `search_engine.py`: Use to test if new data is retrievable.
