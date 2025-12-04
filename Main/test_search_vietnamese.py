from duckduckgo_search import DDGS
import json

def test_search():
    queries = [
        "Once Human ra mắt năm nào",
        "game Once Human ra mắt năm nào", 
        "Once Human release date",
        "Once Human game 2024"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"🔍 Testing: '{query}'")
        print(f"{'='*60}")
        
        try:
            with DDGS() as ddgs:
                # Test với region vn-vi như code hiện tại
                results = list(ddgs.text(query, max_results=5, backend="html", region="vn-vi"))
                
                if not results:
                    print("❌ No results found with region='vn-vi'.")
                    
                    # Thử lại không có region
                    print("⚙️ Trying without region...")
                    results = list(ddgs.text(query, max_results=5, backend="html"))
                    
                if not results:
                    print("❌ Still no results.")
                else:
                    print(f"✅ Found {len(results)} results:")
                    for i, r in enumerate(results):
                        print(f"\n[{i+1}] {r.get('title')}")
                        print(f"    {r.get('body')[:100]}...")
                        print(f"    🔗 {r.get('href')}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_search()
