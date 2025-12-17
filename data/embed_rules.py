import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        RecursiveCharacterTextSplitter = None

# Load Environment Variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in .env")

# Configuration
RULES_FILE = "data/rules/comprehensive_rules.txt"
CHROMA_DB_DIR = "data/chroma_db"
COLLECTION_NAME = "rules_v1"
EMBED_MODEL_NAME = "models/text-embedding-004"

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

def index_rules():
    # 1. Load Data
    documents = load_and_split_rules()
    if not documents:
        return

    # 2. Setup Embedding
    print(f"Loading Embedding Model: {EMBED_MODEL_NAME}...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBED_MODEL_NAME,
        google_api_key=GOOGLE_API_KEY
    )

    # 3. Create/Update Vector Store
    print(f"Indexing Rules to ChromaDB at {CHROMA_DB_DIR} (Collection: {COLLECTION_NAME})...")
    
    # We don't have stable IDs for chunks, so we'll let Chroma generate them or just add.
    # Ideally we'd hash the content for IDs to prevent duplicates on re-run, 
    # but for now we'll just allow overwriting by clearing or assuming clean state.
    # To avoid duplicates in a simple way without complex logic, let's just create the client and delete collection first?
    # No, that might wipe other data if shared DB.
    # Safer: just add. (For demo we won't overengineer de-dupe).
    
    vectorstore = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory=CHROMA_DB_DIR,
        collection_name=COLLECTION_NAME
    )
    
    print("Indexing Complete!")

if __name__ == "__main__":
    index_rules()
