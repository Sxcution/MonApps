# -*- coding: utf-8 -*-
"""
Test different search approaches for "Once Human"
"""
import sys
sys.path.insert(0, r'C:\Users\Mon\Desktop\Mon\Main')

from duckduckgo_search import DDGS

queries_to_test = [
    ("Once Human game release date", "NO region parameter"),
    ("Once Human video game", "NO region, added 'video game'"),
    ("Once Human game 2024", "NO region, added '2024'"),
]

output_file = r'C:\Users\Mon\Desktop\Mon\Main\test_ddgs_variations.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    for query, description in queries_to_test:
        f.write(f"\n{'='*70}\n")
        f.write(f"QUERY: {query}\n")
        f.write(f"APPROACH: {description}\n")
        f.write(f"{'='*70}\n\n")
        
        try:
            with DDGS() as ddgs:
                # Try with NO region parameter at all
                results = list(ddgs.text(query, max_results=5, backend="html"))
                
                for i, r in enumerate(results, 1):
                    f.write(f"\n[{i}] {r['title']}\n")
                    f.write(f"URL: {r['href']}\n")
                    f.write(f"Snippet: {r['body'][:150]}...\n")
                    
                # Check if any result is about the video game
                game_found = False
                for r in results:
                    if "video game" in r['title'].lower() or "video game" in r['body'].lower():
                        game_found = True
                        break
                
                if game_found:
                    f.write("\n[PASS] Found video game results\n")
                else:
                    f.write("\n[FAIL] No video game results\n")
                    
        except Exception as e:
            f.write(f"\nERROR: {e}\n")

print(f"Results saved to: {output_file}")
print("Opening file...")

# Auto-open for user to see
import subprocess
subprocess.run(['notepad.exe', output_file])
