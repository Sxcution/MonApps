"""
Markdown rendering utilities for AI chatbot.
Handles markdown to HTML conversion with syntax highlighting.
"""

from markdown2 import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
import re


def get_dark_theme_style():
    """Return CSS for dark theme code highlighting"""
    return """
    <style>
    /* Pygments Dark Theme (Code Blocks) */
    .codehilite { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 6px; overflow-x: auto; margin: 8px 0; border: 1px solid #333; }
    .codehilite pre { margin: 0; padding: 0; }
    
    /* Syntax Highlighting Colors */
    .codehilite .hll { background-color: #3e3e3e; }
    .codehilite .c { color: #6a9955; font-style: italic; }
    .codehilite .k { color: #569cd6; }
    .codehilite .o { color: #d4d4d4; }
    .codehilite .s { color: #ce9178; }
    .codehilite .kt { color: #4ec9b0; }
    .codehilite .nf { color: #dcdcaa; }
    
    /* GLOBAL TEXT STYLING - TRANSPARENT & CLEAN */
    body { 
        background-color: transparent !important; 
        color: #e0e0e0; /* Bright text for dark mode */
        margin: 0; 
        padding: 0; 
        line-height: 1.5;
    }
    
    /* Normal paragraphs - No background, no padding */
    p { 
        background-color: transparent !important;
        margin: 4px 0; 
    }
    
    /* Ensure code blocks KEEP their background */
    .codehilite {
        background-color: #1e1e1e !important;
    }
    
    /* Links - Blue & Clickable */
    a { color: #4fc1ff; text-decoration: none; font-weight: 500; }
    a:hover { text-decoration: underline; }
    
    /* Inline Code - Subtle highlight */
    code { 
        background: rgba(255, 255, 255, 0.1); 
        color: #dcdcaa; 
        padding: 2px 5px; 
        border-radius: 4px; 
        font-family: 'Consolas', monospace; 
        font-size: 0.95em;
    }
    
    /* Blockquotes - Border left */
    blockquote { 
        border-left: 3px solid #0078d4; 
        padding-left: 10px; 
        color: #b0b0b0; 
        margin: 8px 0; 
        font-style: italic;
    }
    
    /* Tables - Clean borders */
    table { border-collapse: collapse; width: 100%; margin: 8px 0; border: 1px solid #444; }
    th { background: rgba(255, 255, 255, 0.1); font-weight: bold; text-align: left; padding: 6px; border: 1px solid #444; }
    td { border: 1px solid #444; padding: 6px; }
    
    /* Lists */
    ul, ol { padding-left: 20px; margin: 4px 0; }
    li { margin-bottom: 2px; }
    
    /* Headers */
    h1, h2, h3 { color: #ffffff; margin-top: 12px; margin-bottom: 6px; font-weight: 600; }
    h1 { font-size: 1.3em; border-bottom: 1px solid #444; padding-bottom: 4px; }
    h2 { font-size: 1.2em; }
    h3 { font-size: 1.1em; }
    </style>
    """


def markdown_to_html(text: str) -> str:
    """
    Convert markdown text to HTML with syntax highlighting for code blocks.
    
    Args:
        text: Raw markdown text
        
    Returns:
        HTML string with highlighted code blocks
    """
    # DISABLE MARKDOWN - Return plain text as requested
    return f"<div>{text}</div>"


def extract_plain_text(markdown_text: str) -> str:
    """
    Extract plain text from markdown (for copying).
    
    Args:
        markdown_text: Raw markdown text
        
    Returns:
        Plain text without markdown formatting
    """
    # Remove code blocks
    text = re.sub(r'```.*?```', '', markdown_text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    return text.strip()
