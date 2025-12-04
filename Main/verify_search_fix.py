"""
Quick test for smart language search fix
"""
import sys
sys.path.insert(0, r'C:\Users\Mon\Desktop\Mon\Main')

from core.system_controller import SystemController

print("="*70)
print("TESTING: Once Human game release date (English)")
print("Expected: Should detect international query and return game info")
print("="*70)

result = SystemController.web_search("Once Human game release date")

# Check if result contains relevant keywords
if "Once Human" in result and ("2024" in result or "July" in result or "video game" in result):
    print("\n✅ TEST PASSED: Found relevant game information")
    print(f"\nFirst 300 chars of result:\n{result[:300]}")
else:
    print("\n❌ TEST FAILED: Did not find game information") 
    print(f"\nFirst 500 chars of result:\n{result[:500]}")

print("\n" + "="*70)
print("If the test passed, the search fix is working correctly!")
print("="*70)
