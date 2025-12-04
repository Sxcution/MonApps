# -*- coding: utf-8 -*-
"""
Direct test - no emoji to avoid encoding issues
"""
import sys
import os

# Force reload
if 'core.system_controller' in sys.modules:
    del sys.modules['core.system_controller']

sys.path.insert(0, r'C:\Users\Mon\Desktop\Mon\Main')

from core.system_controller import SystemController

print("="*70)
print("TEST: SystemController.web_search")
print("="*70)

# Test English query
query = "Once Human game release date"
print(f"\nQuery: {query}")
print("\nCalling web_search...")

result = SystemController.web_search(query)

# Save to file to avoid console encoding issues
output_file = r'C:\Users\Mon\Desktop\Mon\Main\test_output.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("QUERY: " + query + "\n")
    f.write("="*70 + "\n")
    f.write(result)
    f.write("\n" + "="*70 + "\n")
    
    # Check result
    if "video game" in result.lower() or "2024" in result or "july" in result.lower():
        f.write("\n[PASS] Found game information\n")
        print("\n[PASS] Found game information")
    else:
        f.write("\n[FAIL] Wrong results - still showing grammar content\n")
        print("\n[FAIL] Wrong results")

print(f"\nFull output saved to: {output_file}")
print("Check that file for details")
