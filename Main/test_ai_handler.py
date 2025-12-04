# -*- coding: utf-8 -*-
"""
Test AI Handler để xem có trả lời đúng không
"""
import sys
import os
import json

# Force reload modules
for mod in list(sys.modules.keys()):
    if 'core.' in mod or 'launcher_ui.' in mod:
        del sys.modules[mod]

sys.path.insert(0, r'C:\Users\Mon\Desktop\Mon\Main')

from core.ai_handler import AIHandler

# Load API key
settings_path = r'C:\Users\Mon\Desktop\Mon\Main\launcher_ui\chat_settings.json'
with open(settings_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)
    api_key = settings['api_keys'][0]['key']

print("Initializing AI Handler...")
ai = AIHandler(api_key, "gemini-2.5-flash")

print("\n" + "="*70)
print("TEST 1: Once Human game")
print("="*70)

query1 = "game Once Human ra mat nam nao"
print(f"\nQuery: {query1}")
print("Processing...")

response1 = ai.process_message(query1)

# Save response
output_file = r'C:\Users\Mon\Desktop\Mon\Main\test_ai_response.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("QUERY 1: " + query1 + "\n")
    f.write("="*70 + "\n")
    f.write(response1)
    f.write("\n\n" + "="*70 + "\n\n")
    
    # Check if correct
    if "2024" in response1 or "july" in response1.lower() or "thang 7" in response1.lower():
        f.write("[PASS] AI answered correctly about game release date\n")
        print("[PASS] AI answered correctly")
    else:
        f.write("[FAIL] AI still gives wrong answer\n")
        print("[FAIL] AI wrong answer")

print("\n" + "="*70)
print("TEST 2: WeChat account warming")
print("="*70)

query2 = "cach nuoi tai khoan wechat"
print(f"\nQuery: {query2}")
print("Processing...")

response2 = ai.process_message(query2)

with open(output_file, 'a', encoding='utf-8') as f:
    f.write("\n\nQUERY 2: " + query2 + "\n")
    f.write("="*70 + "\n")
    f.write(response2)
    f.write("\n\n")

print(f"\nResponses saved to: {output_file}")
print("\nCheck console output for tool calls...")
