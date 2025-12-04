# -*- coding: utf-8 -*-
"""
Test DIFFERENT backends for DuckDuckGo
The HTML backend seems to be broken for certain queries from Vietnam
"""
import sys
sys.path.insert(0, r'C:\Users\Mon\Desktop\Mon\Main')

from duckduckgo_search import DDGS

query = "Once Human game release date"
backends_to_test = ["html", "lite", "api"]

output_file = r'C:\Users\Mon\Desktop\Mon\Main\test_backends.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    for backend in backends_to_test:
        f.write(f"\n{'='*70}\n")
        f.write(f"BACKEND: {backend}\n")
        f.write(f"QUERY: {query}\n")
        f.write(f"{'='*70}\n\n")
        
        try:
            with DDGS() as ddgs:
                # NO region parameter
                results = list(ddgs.text(query, max_results=5, backend=backend))
                
                if not results:
                    f.write(f"[NO RESULTS] Backend '{backend}' returned nothing\n")
                    continue
               
                for i, r in enumerate(results, 1):
                    f.write(f"\n[{i}] {r['title']}\n")
                    f.write(f"URL: {r['href']}\n")
                    f.write(f"Snippet: {r['body'][:150]}...\n")
                    
                # Check results
                game_found = any("video game" in r['title'].lower() or "video game" in r['body'].lower()
                                or "wiki" in r['href'].lower() for r in results)
                                
                if game_found:
                    f.write(f"\n✅ [PASS] Backend '{backend}' found game info\n")
                else:
                    # Check if it's Chinese grammar results
                    is_chinese_grammar = any("百度" in r['href'] or "zhidao" in r['href'] for r in results)
                    if is_chinese_grammar:
                        f.write(f"\n❌ [FAIL] Backend '{backend}' returns Chinese grammar\n")
                    else:
                        f.write(f"\n⚠️ [UNKNOWN] Backend '{backend}' returns other content\n")
                        
        except Exception as e:
            f.write(f"\nERROR with backend '{backend}': {e}\n")

print(f"Test complete. Results: {output_file}")

# Open for user
import subprocess
subprocess.run(['notepad.exe', output_file])
