import argparse
import sys
import os

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from search_engine import OptcgSearchEngine

def main():
    parser = argparse.ArgumentParser(description="Query One Piece Card Game Vector DB with Filters")
    parser.add_argument("query", type=str, help="The search query (e.g., 'Luffy Rush')")
    parser.add_argument("--k", type=int, default=10, help="Number of results")
    
    # Filters
    parser.add_argument("--color", type=str, help="Filter by Color (e.g., Red)")
    parser.add_argument("--type", type=str, help="Filter by Card Type (e.g., Character)")
    parser.add_argument("--cost", type=str, help="Filter by Cost (e.g., 5)")
    parser.add_argument("--power", type=str, help="Filter by Power (e.g., 6000)")
    parser.add_argument("--set", type=str, help="Filter by Group ID")
    parser.add_argument("--name", type=str, help="Filter by exact Name (e.g., Nami)")
    parser.add_argument("--provider", type=str, help="Embedding Provider (google_genai or huggingface)")

    args = parser.parse_args()

    # Build Filter Dict
    filters = {}
    if args.color: filters["color"] = args.color
    if args.type: filters["type"] = args.type
    if args.cost: filters["cost"] = args.cost
    if args.power: filters["power"] = args.power
    if args.set: filters["set"] = args.set
    if args.name: filters["name"] = args.name

    try:
        engine = OptcgSearchEngine(provider=args.provider)
        results = engine.search(args.query, filters=filters, k=args.k)

        if not results:
            print("No results found.")
            return

        print("-" * 50)
        for i, doc in enumerate(results):
            meta = doc.metadata
            print(f"Result {i+1}: {meta.get('name', 'Unknown')} ({meta.get('card_type', 'Unknown')})")
            print(f"ID: {meta.get('id')} | Set: {meta.get('groupId')}")
            print(f"Color: {meta.get('color')} | Cost: {meta.get('cost')} | Power: {meta.get('power')}")
            print(f"Effect: {doc.page_content.split('Effect: ')[-1][:100]}...") 
            print("-" * 50)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
