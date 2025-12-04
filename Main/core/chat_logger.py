import json
import os
from datetime import datetime
import uuid

class ChatLogger:
    """
    Handles logging of chat sessions, including user messages, AI responses,
    and internal tool usage (search queries, results) for debugging.
    """
    def __init__(self, log_dir="saved_chats"):
        self.log_dir = log_dir
        self.current_session_id = None
        self.current_log_file = None
        self.session_data = {
            "session_id": "",
            "start_time": "",
            "turns": []
        }
        
        # Create log directory if not exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def start_new_session(self):
        """Start a new chat session."""
        self.current_session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_data = {
            "session_id": self.current_session_id,
            "start_time": datetime.now().isoformat(),
            "turns": []
        }
        self.current_log_file = os.path.join(self.log_dir, f"chat_{timestamp}.json")
        self._save_log()

    def log_turn(self, role: str, content: str, metadata: dict = None):
        """
        Log a single turn (user or model).
        metadata can include: search_queries, search_results, tool_calls, etc.
        """
        if not self.current_session_id:
            self.start_new_session()
            
        turn = {
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "content": content
        }
        
        if metadata:
            turn["metadata"] = metadata
            
        self.session_data["turns"].append(turn)
        self._save_log()

    def _save_log(self):
        """Save current session data to JSON file."""
        if self.current_log_file:
            try:
                with open(self.current_log_file, "w", encoding="utf-8") as f:
                    json.dump(self.session_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"❌ ChatLogger: Failed to save log: {e}")

    def get_all_sessions(self):
        """Return list of all saved sessions (files)."""
        if not os.path.exists(self.log_dir):
            return []
            
        files = [f for f in os.listdir(self.log_dir) if f.endswith(".json")]
        files.sort(reverse=True) # Newest first
        return files

    def load_session(self, filename):
        """Load a specific session log."""
        filepath = os.path.join(self.log_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None
