import os
import json
import glob
import sys
import argparse
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
# Import our new provider
from embedding_provider import get_embedding_settings

# Load Environment Variables
load_dotenv()

# Configuration (Now dynamic)
DATA_DIR = "data/raw_json"

def load_cards():
    cards = []
    pattern = os.path.join(DATA_DIR, "cards_*.json")
    files = glob.glob(pattern)
    print(f"Found {len(files)} JSON files.")
    
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    cards.extend(data)
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            
    print(f"Total raw cards loaded: {len(cards)}")
    return cards

def clean_and_deduplicate(cards):
    """
    Filters duplicates based on 'Number' field (e.g., ST01-001).
    Keeps the first occurrence found.
    """
    unique_cards = []
    seen_numbers = set()
    skipped_count = 0
    
    for card in cards:
        # Extract Number from extendedData
        ext_map = {d["name"]: d["value"] for d in card.get("extendedData", [])}
        card_number = ext_map.get("Number")
        
        if not card_number:
            # Skip cards without a number (shouldn't happen for valid cards)
            continue
            
        if card_number in seen_numbers:
            skipped_count += 1
            continue
            
        seen_numbers.add(card_number)
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
    
    # Extract extended data
    ext_map = {d["name"]: d["value"] for d in card.get("extendedData", [])}
    
    card_type = ext_map.get("CardType", "Unknown")
    color = ext_map.get("Color", "N/A")
    effect = ext_map.get("Description", "")
    traits = ext_map.get("Subtypes", "")
    power = ext_map.get("Power", "N/A")
    counter = ext_map.get("Counterplus", "N/A")
    cost = ext_map.get("Cost", "N/A")
    attr = ext_map.get("Attribute", "N/A")
    
    # HTML cleanup (simple)
    effect = effect.replace("<br>", "\n").replace("<strong>", "").replace("</strong>", "")
    
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
    print("Running Data Cleaning & Deduplication...")
    unique_cards = clean_and_deduplicate(raw_cards)

    if dry_run:
        print("\n[DRY RUN] Skipping Embedding and Indexing.")
        print(f"Would index to: {db_path} ({collection_name})")
        print("Verification Successful.")
        return

    documents = []
    for card in unique_cards:
        # Prepare Metadata (for Structured Search)
        ext_map = {d["name"]: d["value"] for d in card.get("extendedData", [])}
        
        metadata = {
            "productId": card.get("productId"),
            "groupId": card.get("groupId"),
            "name": card.get("name"),
            "card_type": ext_map.get("CardType", "Unknown"),
            "color": ext_map.get("Color", "Unknown"),
            "cost": ext_map.get("Cost", "0"),
            "power": ext_map.get("Power", "0"),
            "attribute": ext_map.get("Attribute", "Unknown"),
            "number": ext_map.get("Number", "Unknown")
        }
        
        # Prepare Content (for Vector Search)
        page_content = format_card_text(card)
        
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)
        
    print(f"Prepared {len(documents)} documents for indexing.")
    
    # 2. Setup Embedding (from provider)
    print(f"Loading Embedding Model...")
    
    # Collect IDs for Upsert
    ids = [str(d.metadata["productId"]) for d in documents]

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
    parser = argparse.ArgumentParser(description="Update Vector DB with Deduplication")
    parser.add_argument("--dry-run", action="store_true", help="Run cleaning check without indexing")
    parser.add_argument("--provider", type=str, help="Override embedding provider (google_genai or huggingface)")
    args = parser.parse_args()
    
    process_and_index(dry_run=args.dry_run, provider=args.provider)
