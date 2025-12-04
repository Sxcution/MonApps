"""
AIChat - Intelligent AI Chatbot Module
Entry point for the AI Chat interface
"""

from .ui.chat_window import ChatBubble

def create_chat_interface(parent=None):
    """
    Factory function to create and return a ChatBubble instance.
    
    Args:
        parent: Parent widget (QWidget) for the chat bubble
        
    Returns:
        ChatBubble instance
    """
    return ChatBubble(parent)

# Export for easy import
__all__ = ['ChatBubble', 'create_chat_interface']
