import pytest
import os
import sys

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.search import HybridSearchService

# Check if DB exists to skip tests if not ready
DB_PATH = "data/chroma_db"
DB_READY = os.path.exists(DB_PATH) and len(os.listdir(DB_PATH)) > 0

@pytest.mark.skipif(not DB_READY, reason="ChromaDB data not found")
def test_initialize_search():
    service = HybridSearchService(persist_directory=DB_PATH)
    assert service.vector_store is not None

@pytest.mark.skipif(not DB_READY, reason="ChromaDB data not found")
def test_simple_search():
    service = HybridSearchService(persist_directory=DB_PATH)
    results = service.hybrid_search("Luffy", k=1)
    assert isinstance(results, list)
    if results:
        assert "content" in results[0]
        assert "metadata" in results[0]

@pytest.mark.skipif(not DB_READY, reason="ChromaDB data not found")
def test_search_with_filters():
    service = HybridSearchService(persist_directory=DB_PATH)
    # Search for Red cards
    results = service.hybrid_search("Luffy", k=5, filters={"color": "Red"})
    for res in results:
        # Chroma metadata filter is precise for exact matches
        assert res["metadata"].get("color") == "Red"

@pytest.mark.skipif(not DB_READY, reason="ChromaDB data not found")
def test_retrieve_format():
    service = HybridSearchService(persist_directory=DB_PATH)
    text = service.retrieve_card_data("Luffy")
    assert isinstance(text, str)
    assert len(text) > 0
