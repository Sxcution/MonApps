"""
Direct test với AI Handler để xem search fix có hoạt động không
Bypass UI để test trực tiếp
"""
import sys
import os

# Force reload modules
if 'core.system_controller' in sys.modules:
    del sys.modules['core.system_controller']
if 'core.ai_handler' in sys.modules:
    del sys.modules['core.ai_handler']

sys.path.insert(0, r'C:\Users\Mon\Desktop\Mon\Main')

from core.system_controller import SystemController
from core.ai_handler import AIHandler

print("="*70)
print("TEST 1: SystemController.web_search trực tiếp")
print("="*70)

# Test 1: Direct SystemController call
query1 = "Once Human game release date"
print(f"\nQuery: {query1}")
result1 = SystemController.web_search(query1)

# Check kết quả
if "video game" in result1.lower() or "2024" in result1 or "july" in result1.lower():
    print("\n✅ PASS: Tìm được thông tin game")
    print(f"Snippet: {result1[:400]}")
else:
    print("\n❌ FAIL: Vẫn trả về kết quả sai")
    print(f"Result: {result1[:500]}")

print("\n" + "="*70)
print("TEST 2: Query tiếng Việt")
print("="*70)

query2 = "giá vàng hôm nay"
print(f"\nQuery: {query2}")
result2 = SystemController.web_search(query2)

if "vàng" in result2.lower() and ("sjc" in result2.lower() or "triệu" in result2.lower()):
    print("\n✅ PASS: Tìm được thông tin giá vàng")
else:
    print("\n❌ FAIL: Không tìm được giá vàng")

print("\n" + "="*70)
print("TEST 3: AI Handler với Gemini API")
print("="*70)

# Đọc API key từ settings
import json
settings_path = r'C:\Users\Mon\Desktop\Mon\Main\launcher_ui\chat_settings.json'
with open(settings_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)
    api_key = settings['api_keys'][0]['key']

print(f"\nKhởi tạo AI Handler...")
ai = AIHandler(api_key, "gemini-2.5-flash")

# Test với query về Once Human
query3 = "game Once Human ra mắt năm nào"
print(f"\nGửi query tới Gemini: {query3}")
print("Đang xử lý...")

try:
    response = ai.process_message(query3)
    print(f"\n📤 Response từ AI:\n{response}")
    
    # Check response có chứa thông tin đúng không
    if "2024" in response or "july" in response.lower() or "tháng 7" in response.lower():
        print("\n✅ AI TRẢ LỜI ĐÚNG!")
    else:
        print("\n❌ AI VẪN TRẢ LỜI SAI!")
        
except Exception as e:
    print(f"\n❌ Lỗi: {e}")

print("\n" + "="*70)
