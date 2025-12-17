import argparse
from dotenv import load_dotenv
from langchain_chroma import Chroma
import sys
import os

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import our new provider
from data.embedding_provider import get_embedding_settings

class OptcgSearchEngine:
    def __init__(self, provider=None):
        load_dotenv()
        
        # Get settings dynamically
        try:
            self.embeddings, self.db_path, self.collection_name, self.provider_name = get_embedding_settings(provider)
        except ValueError as e:
            raise ValueError(f"Failed to initialize search engine: {e}")

        if not os.path.exists(self.db_path):
             # Just a warning, maybe we haven't indexed yet
             print(f"Warning: Database path {self.db_path} does not exist yet.")

        self.vectorstore = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
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
        
        print(f"DEBUG: Searching '{query_text}' using model '{self.provider_name}' with filter: {filter_arg}")
        
        results = self.vectorstore.similarity_search(
            query=query_text,
            k=k,
            filter=filter_arg
        )
        
        return results
