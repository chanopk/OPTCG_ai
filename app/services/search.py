import os
from langchain_chroma import Chroma
from data.embedding_provider import get_embedding_settings

class HybridSearchService:
    def __init__(self, provider=None):
        # Initialize Embeddings and DB Path dynamically
        try:
            self.embedding_function, self.db_path, self.collection_name, self.provider_name = get_embedding_settings(provider)
        except ValueError as e:
            print(f"Error initializing HybridSearchService: {e}")
            raise e
        
        # Initialize Vector Store (Chroma) for Cards
        self.vector_store = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embedding_function,
            collection_name=self.collection_name
        )
        
        # Initialize Vector Store for Rules
        # Assuming rules share the same DB path but different collection
        try:
            self.rules_store = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embedding_function,
                collection_name="rules_v1"
            )
        except Exception as e:
            print(f"Warning: Could not initialize Rules store: {e}")
            self.rules_store = None

    def hybrid_search(self, query: str, k: int = 5, filters: dict = None) -> list:
        """
        Performs a similarity search combined with metadata filtering.
        """
        # Perform Search
        try:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=filters
            )
            
            output = []
            for doc, score in results:
                item = {
                    "score": float(score),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                output.append(item)
                
            return output
            
        except Exception as e:
            print(f"Search Error: {e}")
            return []

    def retrieve_card_data(self, query: str, filters: dict = None) -> str:
        """
        High-level retrieval function for Agents. Returns a formatted string context.
        """
        results = self.hybrid_search(query, k=25, filters=filters)
        
        if not results:
            return "No card data found."
            
        context_parts = []
        for i, res in enumerate(results):
            meta = res["metadata"]
            name = meta.get("name", "Unknown")
            pid = meta.get("productId")
            context_parts.append(f"Card {i+1} (ID: {pid}):\n{res['content']}\n")
            
        return "\n---\n".join(context_parts)

    def retrieve_rules(self, query: str, k: int = 4) -> str:
        """
        Retrieves relevant rule sections based on a query.
        """
        if not self.rules_store:
            return "Rule knowledge base is not available."

        try:
            results = self.rules_store.similarity_search_with_score(query, k=k)
            
            context_parts = []
            for doc, score in results:
                # doc.page_content contains the rule text chunk
                context_parts.append(doc.page_content)
                
            if not context_parts:
                return "No specific rules found matching that query."

            return "Relevant Rules:\n" + "\n---\n".join(context_parts)
            
        except Exception as e:
            print(f"Rule Search Error: {e}")
            return f"Error searching rules: {e}"
