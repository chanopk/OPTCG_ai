import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class HybridSearchService:
    def __init__(self, persist_directory="data/chroma_db", collection_name="optcg_cards_v1"):
        # Configure Google API Key
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Initialize Embedding Model (Google Gemini) - Must match ingestion script
        self.embedding_function = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.google_api_key
        )
        
        # Initialize Vector Store (Chroma) for Cards
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_function,
            collection_name=collection_name
        )
        
        # Initialize Vector Store for Rules
        try:
            self.rules_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding_function,
                collection_name="rules_v1"
            )
        except Exception as e:
            print(f"Warning: Could not initialize Rules store: {e}")
            self.rules_store = None

    def hybrid_search(self, query: str, k: int = 5, filters: dict = None) -> list:
        """
        Performs a similarity search combined with metadata filtering.
        
        Args:
            query (str): The search query (e.g. "Red Character with 6000 Power")
            k (int): Number of results to return
            filters (dict): Metadata filters (e.g. {"color": "Red", "cost": "5"})
                            ChromaDB supports operators too, but simple dict implies exact match.
        
        Returns:
            list: List of dictionaries containing score, content, and metadata.
        """
        # Perform Search
        # similarity_search_with_score returns (Document, score) tuples.
        # Lower score is better (distance), but Chroma might normalize. 
        # Actually Chroma default is L2 distance (lower is better).
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
        results = self.hybrid_search(query, k=5, filters=filters)
        
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
