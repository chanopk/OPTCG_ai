import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class HybridSearchService:
    def __init__(self, persist_directory="data/chroma_db", collection_name="optcg_cards_v1"):
        # Initialize Embedding Model (Local)
        # This will download the model if not present
        self.embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Initialize Vector Store (Chroma)
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_function,
            collection_name=collection_name
        )

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
