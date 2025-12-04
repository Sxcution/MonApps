"""
Test script to verify the smart language detection in web_search function
"""
import sys
sys.path.insert(0, r'C:\Users\Mon\Desktop\Mon\Main')

from core.system_controller import SystemController

def test_search_fix():
    print("=" * 70)
    print("Testing Smart Language Detection in web_search")
    print("=" * 70)
    
    test_queries = [
        ("Once Human game release date", "Should use wt-wt (international)"),
        ("game Once Human ra mat nam nao", "Should use wt-wt (international, no Vietnamese chars)"),
        ("giá vàng hôm nay", "Should use vn-vi (Vietnamese keywords + chars)"),
        ("thời tiết Hà Nội", "Should use vn-vi (Vietnamese)"),
    ]
    
    for query, expected in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: '{query}'")
        print(f"Expected: {expected}")
        print(f"{'='*70}")
        
        result = SystemController.web_search(query)
        
        # Show first 500 chars of result
        print(f"\nResult (first 500 chars):")
        print(result[:500])
        print("\n" + "="*70)
        input("Press Enter to continue to next test...")

if __name__ == "__main__":
    test_search_fix()
