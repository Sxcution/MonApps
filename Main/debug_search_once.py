from duckduckgo_search import DDGS
import json

def test_search():
    query = "Once Human game release date"
    print(f"🔍 Testing search for: '{query}' using backend='html'...")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5, backend="html"))
            
            if not results:
                print("❌ No results found.")
                return

            print(f"✅ Found {len(results)} results:")
            for i, r in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(f"Title: {r.get('title')}")
                print(f"URL: {r.get('href')}")
                print(f"Snippet: {r.get('body')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_search()
