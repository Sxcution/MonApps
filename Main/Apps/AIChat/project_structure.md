# Project Structure - AIChat

AI-powered chatbot module using Google Gemini API.

## Files
- `main.py`: Entry point, ChatBubble widget (floating chat button)

## Sub-directories
- `core/`: Core functionality
    - `ai_handler.py`: Gemini API communication, function calling, tool execution
    - `chat_logger.py`: Chat session logging and history
    - `markdown_utils.py`: Markdown rendering utilities
- `ui/`: UI components
    - `chat_window.py`: Main chat window interface
- `config/`: Configuration
    - `chat_settings.json`: API keys, model settings
- `data/`: Data storage
    - `saved_chats/`: Chat history JSON files

## Key Features
- Floating chat bubble (draggable)
- Detach to overlay mode
- Function calling (web search, system control)
- Chat history persistence

## Dependencies
- PySide6
- google-generativeai
- duckduckgo_search
