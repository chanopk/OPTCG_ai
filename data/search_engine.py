import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Configuration
CHROMA_DB_DIR = "data/chroma_db"
COLLECTION_NAME = "optcg_cards_v1"
EMBED_MODEL_NAME = "models/text-embedding-004"

class OptcgSearchEngine:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env")
            
        if not os.path.exists(CHROMA_DB_DIR):
            raise FileNotFoundError(f"ChromaDB not found at {CHROMA_DB_DIR}")

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBED_MODEL_NAME,
            google_api_key=self.api_key
        )
        
        self.vectorstore = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=self.embeddings,
            collection_name=COLLECTION_NAME
        )

    def search(self, query_text: str, filters: dict = None, k: int = 5):
        """
        Performs a hybrid search: Semantic Query + Metadata Filters.
        
        filters: dict -> { "color": "Red", "cost": "5", "type": "Character" }
        """
        # Construct ChromaDB where clause
        where_clause = {}
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if value:
                    # Map common keys to metadata field names if they differ
                    # Our metadata keys: card_type, color, cost, power, attribute, groupId
                    
                    if key.lower() == "type":
                        conditions.append({"card_type": value})
                    elif key.lower() == "color":
                        conditions.append({"color": value})
                    elif key.lower() == "set":
                        conditions.append({"groupId": value})
                    else:
                        # Fallback for direct match (cost, power, etc.)
                        conditions.append({key: value})
            
            if len(conditions) == 1:
                where_clause = conditions[0]
            elif len(conditions) > 1:
                where_clause = {"$and": conditions}

        # Perform Search
        # If no where_clause, pass None
        filter_arg = where_clause if where_clause else None
        
        print(f"DEBUG: Searching '{query_text}' with filter: {filter_arg}")
        
        results = self.vectorstore.similarity_search(
            query=query_text,
            k=k,
            filter=filter_arg
        )
        
        return results
