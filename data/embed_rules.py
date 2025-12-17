import os
import argparse
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        RecursiveCharacterTextSplitter = None

# Import our new provider
from embedding_provider import get_embedding_settings

# Load Environment Variables
load_dotenv()
RULES_FILE = "data/rules/comprehensive_rules.txt"

def load_and_split_rules():
    if not os.path.exists(RULES_FILE):
        print(f"Error: Rules file not found at {RULES_FILE}")
        return []

    with open(RULES_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    if RecursiveCharacterTextSplitter:
        print("Using RecursiveCharacterTextSplitter")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n## ", "\n### ", "\n", " ", ""],
            is_separator_regex=False
        )
        texts = text_splitter.create_documents([text])
    else:
        print("Fallback: Using manual splitting")
        # Simple split by sections
        raw_chunks = text.split("\n## ")
        texts = []
        for chunk in raw_chunks:
            if not chunk.strip(): continue
            content = "## " + chunk if not chunk.startswith("##") else chunk
            texts.append(Document(page_content=content, metadata={"source": "rules"}))
    
    print(f"Split rules into {len(texts)} chunks.")
    return texts

def index_rules(provider=None):
    # 0. Get Settings
    try:
        embeddings, db_path, collection_name, provider_name = get_embedding_settings(provider)
        # Use a specific collection for rules, distinct from cards but in the same DB or separate?
        # The project originally used "rules_v1".
        # If we use the SAME db_path as cards, we assume it can hold multiple collections.
        # Chroma supports multiple collections in one persistence directory.
        rules_collection_name = "rules_v1" 
        
        print(f"Using Provider: {provider_name}")
        print(f"Target DB Path: {db_path} (Collection: {rules_collection_name})")
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return

    # 1. Load Data
    documents = load_and_split_rules()
    if not documents:
        return

    # 3. Create/Update Vector Store
    print(f"Indexing Rules to ChromaDB...")
    
    vectorstore = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory=db_path,
        collection_name=rules_collection_name
    )
    
    print("Indexing Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Rules Vector DB")
    parser.add_argument("--provider", type=str, help="Override embedding provider (google_genai or huggingface)")
    args = parser.parse_args()
    
    index_rules(provider=args.provider)
