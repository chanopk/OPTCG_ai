import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# Load Environment Variables
load_dotenv()

# Constants
DEFAULT_PROVIDER = "google_genai"
DB_ROOT_DIR = "data"

def get_embedding_settings(provider=None):
    """
    Returns a tuple of (embedding_model_instance, chroma_db_path, collection_name)
    based on the selected provider.
    
    provider: "google_genai" or "huggingface". If None, reads from env EMBEDDING_PROVIDER.
    """
    if not provider:
        provider = os.getenv("EMBEDDING_PROVIDER", DEFAULT_PROVIDER).lower()

    if provider == "google_genai":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env for google_genai provider")
            
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        db_path = os.path.join(DB_ROOT_DIR, "chroma_db_gemini")
        collection_name = "optcg_cards_v1"
        
    elif provider == "huggingface":
        # Using a solid default model for local usage
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        db_path = os.path.join(DB_ROOT_DIR, "chroma_db_huggingface")
        collection_name = "optcg_cards_local_v1"
        
    else:
        raise ValueError(f"Unknown embedding provider: {provider}. Use 'google_genai' or 'huggingface'.")

    return embeddings, db_path, collection_name, provider
