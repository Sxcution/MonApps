from core.system_controller import SystemController
from core.chat_logger import ChatLogger
import time
import os

def test_search_fix():
    print("\n🔎 TESTING SEARCH (Query: 'game once human ra mắt khi nào')...")
    # Test with default (current) logic
    print("1. Current Logic (No region):")
    res = SystemController.web_search("game once human ra mắt khi nào")
    print(f"Result length: {len(res)}")
    print(f"Snippet: {res[:200]}...")

    # We will manually test region in the next step if this fails, 
    # but for now let's see what the current multi-backend logic returns.

def test_history_persistence():
    print("\n💾 TESTING HISTORY PERSISTENCE...")
    logger = ChatLogger(log_dir="saved_chats_debug")
    logger.start_new_session()
    session_file = logger.current_log_file
    print(f"Session File: {session_file}")
    
    # Simulate chat
    logger.log_turn("user", "Hello 1")
    logger.log_turn("model", "Hi 1")
    
    # Simulate "Last message before crash"
    print("Logging last message...")
    logger.log_turn("user", "This is the last message")
    
    # Verify immediately reading the file
    with open(session_file, "r", encoding="utf-8") as f:
        content = f.read()
        if "This is the last message" in content:
            print("✅ File contains last message immediately.")
        else:
            print("❌ File MISSING last message!")

if __name__ == "__main__":
    test_search_fix()
    test_history_persistence()
