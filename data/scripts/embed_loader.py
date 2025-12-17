import os
import json
import glob
import sys
import argparse
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
# Import our new provider
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from data.embedding_provider import get_embedding_settings

# Load Environment Variables
load_dotenv()

# Configuration
DATA_DIR = "data/clean_json"

def load_cards():
    cards = []
    pattern = os.path.join(DATA_DIR, "cards_*.json")
    files = glob.glob(pattern)
    print(f"Found {len(files)} JSON files in {DATA_DIR}.")
    
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    cards.extend(data)
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            
    print(f"Total cards loaded: {len(cards)}")
    return cards

def clean_and_deduplicate(cards):
    """
    Filters duplicates based on 'id' field (e.g., OP14-001).
    Keeps the first occurrence found.
    """
    unique_cards = []
    seen_ids = set()
    skipped_count = 0
    
    for card in cards:
        card_id = card.get("id")
        
        if not card_id:
            continue
            
        if card_id in seen_ids:
            skipped_count += 1
            continue
            
        seen_ids.add(card_id)
        unique_cards.append(card)
        
    print(f"Deduplication complete.")
    print(f"  - Unique Cards: {len(unique_cards)}")
    print(f"  - Skipped Duplicates: {skipped_count}")
    
    return unique_cards

def format_card_text(card):
    """
    Combines card fields into a single text for embedding.
    """
    name = card.get("name", "Unknown")
    card_type = card.get("type", "Unknown")
    color = card.get("color", "N/A")
    effect = card.get("effect", "")
    traits = "; ".join(card.get("subtypes", []))
    power = card.get("power", "N/A")
    counter = card.get("counter", "N/A")
    cost = card.get("cost", "N/A")
    attr = card.get("attribute", "N/A")
    
    # New clean schema is already cleaner, but ensuring string parsing
    text = (
        f"Name: {name}\n"
        f"Type: {card_type}\n"
        f"Color: {color}\n"
        f"Cost: {cost}\n"
        f"Power: {power}\n"
        f"Counter: {counter}\n"
        f"Attribute: {attr}\n"
        f"Traits: {traits}\n"
        f"Effect: {effect}"
    )
    return text

def process_and_index(dry_run=False, provider=None):
    # 0. Get Settings
    try:
        embeddings, db_path, collection_name, provider_name = get_embedding_settings(provider)
        print(f"Using Provider: {provider_name}")
        print(f"Target DB Path: {db_path}")
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return

    # 1. Load Data
    raw_cards = load_cards()
    if not raw_cards:
        print("No cards found to index.")
        return

    # 1.5 Cleaning & Deduplication
    print("Running Deduplication...")
    unique_cards = clean_and_deduplicate(raw_cards)

    if dry_run:
        print("\n[DRY RUN] Skipping Embedding and Indexing.")
        print(f"Would index to: {db_path} ({collection_name})")
        print("Verification Successful.")
        return

    documents = []
    for card in unique_cards:
        # Prepare Metadata (for Structured Search)
        # Using flat keys now
        metadata = {
            "id": card.get("id", "Unknown"), # Previously 'number' or 'productId'
            "name": card.get("name"),
            "card_type": card.get("type", "Unknown"),
            "color": card.get("color", "Unknown"),
            "cost": str(card.get("cost", "0")), # Metadata values should be strings or simple types
            "power": str(card.get("power", "0")),
            "attribute": card.get("attribute", "Unknown"),
            "number": card.get("id", "Unknown") # Keeping 'number' key for compatibility if search uses it
        }
        
        # Prepare Content (for Vector Search)
        page_content = format_card_text(card)
        
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)
        
    print(f"Prepared {len(documents)} documents for indexing.")
    
    # 2. Setup Embedding (from provider)
    print(f"Loading Embedding Model...")
    
    # Collect IDs for Upsert - Use Card ID (Number) as Vector ID to prevent duplication
    ids = [d.metadata["id"] for d in documents]

    # 3. Create/Update Vector Store
    print(f"Indexing to ChromaDB at {db_path}...")
    
    vectorstore = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory=db_path,
        collection_name=collection_name,
        ids=ids
    )
    
    print("Indexing Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Vector DB using Clean JSON")
    parser.add_argument("--dry-run", action="store_true", help="Run check without indexing")
    parser.add_argument("--provider", type=str, help="Override embedding provider (google_genai or huggingface)")
    args = parser.parse_args()
    
    process_and_index(dry_run=args.dry_run, provider=args.provider)
