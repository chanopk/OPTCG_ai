import os
import json
import glob
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Load Environment Variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in .env")

# Configuration
DATA_DIR = "data/raw_json"
CHROMA_DB_DIR = "data/chroma_db"
COLLECTION_NAME = "optcg_cards_v1"
EMBED_MODEL_NAME = "models/text-embedding-004" # Gemini Embedding Model

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
            
    print(f"Total cards loaded: {len(cards)}")
    return cards

def format_card_text(card):
    """
    Combines card fields into a single text for embedding.
    Format:
    Name: [Name]
    Type: [CardType]
    Color: [Color]
    Effect: [Description]
    Traits: [Subtypes]
    Power: [Power] / Counter: [Counter]
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

def process_and_index():
    # 1. Load Data
    raw_cards = load_cards()
    if not raw_cards:
        print("No cards found to index.")
        return

    documents = []
    for card in raw_cards:
        # Prepare Metadata (for Structured Search)
        ext_map = {d["name"]: d["value"] for d in card.get("extendedData", [])}
        
        metadata = {
            "productId": card.get("productId"),
            "groupId": card.get("groupId"),
            "name": card.get("name"),
            "card_type": ext_map.get("CardType", "Unknown"),
            "color": ext_map.get("Color", "Unknown"),
            "cost": ext_map.get("Cost", "0"), # Store as string or convert? Chroma handles strings/int/float.
            "power": ext_map.get("Power", "0"),
            "attribute": ext_map.get("Attribute", "Unknown"),
            "number": ext_map.get("Number", "Unknown")
        }
        
        # Prepare Content (for Vector Search)
        page_content = format_card_text(card)
        
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)
        
    print(f"Prepared {len(documents)} documents for indexing.")
    
    # 2. Setup Embedding (Local)
    print(f"Loading Embedding Model: {EMBED_MODEL_NAME}...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBED_MODEL_NAME,
        google_api_key=GOOGLE_API_KEY
    )
    
    # Collect IDs for Upsert
    ids = [str(d.metadata["productId"]) for d in documents]

    # 3. Create/Update Vector Store
    print(f"Indexing to ChromaDB at {CHROMA_DB_DIR}...")
    # Using from_documents with ids ensures UPSERT (Update/Insert) behavior
    vectorstore = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory=CHROMA_DB_DIR,
        collection_name=COLLECTION_NAME,
        ids=ids
    )
    
    print("Indexing Complete!")

if __name__ == "__main__":
    process_and_index()
