from flask import Blueprint, request, jsonify, render_template
import sqlite3
import json
import os
import uuid
from datetime import datetime
from .database import get_db_connection
from app.chatbot_tools import AVAILABLE_TOOLS

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chat')

# --- Helper Functions ---

def get_ai_settings():
    conn = get_db_connection()
    try:
        settings = conn.execute('SELECT key, value FROM ai_settings').fetchall()
        return {row['key']: row['value'] for row in settings}
    except:
        return {}
    finally:
        conn.close()

def save_ai_setting(key, value):
    conn = get_db_connection()
    conn.execute('INSERT OR REPLACE INTO ai_settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_context_data():
    """Fetch relevant data from Dashboard for AI context"""
    conn = get_db_connection()
    
    # 1. Get Notes
    notes = conn.execute('SELECT title_html, content_html, status FROM notes WHERE is_marked = 0 LIMIT 5').fetchall()
    notes_text = "Recent Notes:\n" + "\n".join([f"- [{n['status']}] {n['title_html']}: {n['content_html']}" for n in notes])
    
    # 2. Get Telegram Sessions Status
    sessions = conn.execute('SELECT filename, status_text, is_live FROM session_metadata LIMIT 10').fetchall()
    sessions_text = "Telegram Sessions:\n" + "\n".join([f"- {s['filename']}: {s['status_text']} (Live: {s['is_live']})" for s in sessions])
    
    # 3. Get MXH Accounts
    accounts = conn.execute('SELECT account_name, username, platform FROM mxh_accounts JOIN mxh_cards ON mxh_accounts.card_id = mxh_cards.id LIMIT 10').fetchall()
    accounts_text = "Social Accounts:\n" + "\n".join([f"- {a['platform']}: {a['account_name']} ({a['username']})" for a in accounts])
    
    conn.close()
    
    return f"{notes_text}\n\n{sessions_text}\n\n{accounts_text}"

# --- API Endpoints ---

@chatbot_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """Get list of chat sessions"""
    try:
        conn = get_db_connection()
        # Ensure table exists (migration check)
        try:
            sessions = conn.execute('SELECT id, title, updated_at FROM chat_sessions ORDER BY updated_at DESC').fetchall()
        except sqlite3.OperationalError:
            # Table might not exist yet if running old DB
            return jsonify({'success': True, 'sessions': []})
            
        conn.close()
        return jsonify({'success': True, 'sessions': [dict(row) for row in sessions]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/new', methods=['POST'])
def new_session():
    """Create a new session"""
    try:
        session_id = str(uuid.uuid4())
        conn = get_db_connection()
        conn.execute('INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)',
                     (session_id, 'New Chat', datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'session_id': session_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Get history for a specific session"""
    try:
        conn = get_db_connection()
        history = conn.execute('SELECT role, content, timestamp FROM chat_history WHERE session_id = ? ORDER BY id ASC', (session_id,)).fetchall()
        conn.close()
        return jsonify({'success': True, 'history': [dict(row) for row in history]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/delete_session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'GET':
        return jsonify({'success': True, 'settings': get_ai_settings()})
    
    try:
        data = request.json
        for key, value in data.items():
            save_ai_setting(key, value)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/send', methods=['POST'])
def send_message():
    try:
        data = request.json
        user_message = data.get('message')
        session_id = data.get('session_id')
        request_provider = data.get('provider')  # Get provider from request
        request_model = data.get('model')        # Get model from request
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400

        conn = get_db_connection()
        
        # Create session if not exists or if session_id is missing
        if not session_id:
            session_id = str(uuid.uuid4())
            conn.execute('INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)',
                         (session_id, user_message[:30], datetime.now().isoformat(), datetime.now().isoformat()))
        else:
            # Update session timestamp
            conn.execute('UPDATE chat_sessions SET updated_at = ? WHERE id = ?', (datetime.now().isoformat(), session_id))
            
            # Update title if it's "New Chat" (first message)
            current_title = conn.execute('SELECT title FROM chat_sessions WHERE id = ?', (session_id,)).fetchone()
            if current_title and current_title['title'] == 'New Chat':
                conn.execute('UPDATE chat_sessions SET title = ? WHERE id = ?', (user_message[:30], session_id))

        # 1. Save User Message
        conn.execute('INSERT INTO chat_history (role, content, timestamp, session_id) VALUES (?, ?, ?, ?)', 
                     ('user', user_message, datetime.now().isoformat(), session_id))
        conn.commit()
        # 2. Get Settings & Context
        settings = get_ai_settings()
        # Use request provider/model if provided, otherwise fallback to settings
        provider = request_provider if request_provider else settings.get('provider', 'gemini')
        # Build simple system prompt - NO TOOL INSTRUCTIONS
        base_prompt = settings.get('system_prompt', 'Bạn là Dashboard Assistant - trợ lý thông minh.')
        
        # CRITICAL: Add explicit instruction to NEVER return JSON
        anti_json_instruction = """

QUAN TRỌNG: 
- KHÔNG BAO GIỜ trả lời bằng JSON format
- KHÔNG BAO GIỜ trả về {'action': 'use_tool', ...}
- CHỈ trả lời bằng ngôn ngữ tự nhiên, thân thiện
- Nếu câu hỏi có chứa dữ liệu từ database (trong dấu ngoặc vuông [...]), hãy đọc và tóm tắt cho user
- Trả lời ngắn gọn, súc tích bằng tiếng Việt kèm những icon nếu cần.
"""
        
        system_prompt = base_prompt + anti_json_instruction
        
        # Get context
        context = get_context_data()
        full_system_prompt = f"{system_prompt}\n\nCURRENT DASHBOARD CONTEXT:\n{context}"
        
        # PRE-EXECUTE TOOLS BEFORE CALLING AI
        # Detect and execute tools based on keywords, then inject results into user message
        tool_result_text = ""
        
        # Detect search intent
        if any(kw in user_message.lower() for kw in ['tìm', 'search', 'có', 'xem', 'coi', 'hiển thị']):
            # Extract search keyword intelligently
            import re
            search_kw = None
            
            # Pattern 1: "tìm [ghi chú] có tên X" or "tìm [ghi chú] X"
            # Remove filler words first
            cleaned = user_message.lower()
            cleaned = re.sub(r'ghi\s*chú\s*(có\s*tên|của)?', '', cleaned)  # Remove "ghi chú có tên/của"
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Normalize whitespace
            
            # Now extract after "tìm"
            match = re.search(r'tìm\s+(.+?)(?:\s+không|\?|$)', cleaned)
            if match:
                potential_kw = match.group(1).strip()
                # Handle OR: "thắng nguyễn hoặc check user" → try both
                if 'hoặc' in potential_kw or 'hay' in potential_kw or 'và' in potential_kw:
                    # Split by OR/AND and try first part
                    parts = re.split(r'\s+(?:hoặc|hay|và)\s+', potential_kw)
                    search_kw = parts[0].strip()  # Use first part
                else:
                    search_kw = potential_kw
            
            # Pattern 2: "có <keyword> không"
            if not search_kw:
                match = re.search(r'có\s+(.+?)\s+không', cleaned)
                if match:
                    search_kw = match.group(1).strip()
            
            # Pattern 3: Remove action verbs and take the rest
            if not search_kw:
                # Remove common action verbs
                cleaned = re.sub(r'^(hiển thị|xem|coi|tìm|search)\s+', '', cleaned)
                cleaned = re.sub(r'\s+(?:của|trong)\s+', ' ', cleaned)
                tokens = cleaned.split()
                if len(tokens) >= 1:
                    search_kw = ' '.join(tokens[:4])  # Take up to 4 words
            
            # Execute search if keyword found
            if search_kw and 'ghi chú' in user_message.lower():
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n[SEARCH] Keyword: '{search_kw}'\n")
                
                result = AVAILABLE_TOOLS['search_notes']['function'](search_kw)
                
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"[SEARCH] Result count: {result.get('count', 0)}\n")
                
                if result.get('success'):
                    notes = result.get('notes', [])
                    if notes:
                        import re
                        tool_result_text = f"\n\n[TÔI ĐÃ TÌM THẤY {len(notes)} GHI CHÚ:\n"
                        for note in notes[:5]:  # Limit to 5 results
                            # Strip HTML tags
                            clean_title = re.sub('<.*?>', '', note['title'])
                            clean_content = re.sub('<.*?>', '', note['content'])
                            
                            # Smart snippet extraction
                            snippet = ""
                            if search_kw:
                                # Find keyword in content (case insensitive)
                                idx = clean_content.lower().find(search_kw.lower())
                                if idx != -1:
                                    # Extract around keyword: -100 chars to +400 chars
                                    start = max(0, idx - 100)
                                    end = min(len(clean_content), idx + 400)
                                    snippet = f"...{clean_content[start:end]}..."
                                else:
                                    # Keyword in title, show start of content
                                    snippet = clean_content[:500] + "..."
                            else:
                                snippet = clean_content[:500] + "..."
                                
                            tool_result_text += f"- Tiêu đề: {clean_title}\n  Nội dung: {snippet}\n"
                        tool_result_text += "]"
                    else:
                        tool_result_text = f"\n\n[TÔI ĐÃ TÌM KIẾM NHƯNG KHÔNG TÌM THẤY GHI CHÚ NÀO VỚI TỪ KHÓA '{search_kw}']"
                
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"[SEARCH] Final text: {tool_result_text[:200]}...\n")
        
        # Detect "list all notes" intent
        elif any(phrase in user_message.lower() for phrase in ['tất cả ghi chú', 'all notes', 'danh sách ghi chú']):
            result = AVAILABLE_TOOLS['get_all_notes']['function']()
            if result.get('success'):
                import re
                notes = result.get('notes', [])
                tool_result_text = f"\n\n[DANH SÁCH {len(notes)} GHI CHÚ:\n"
                for note in notes[:10]:  # Limit to 10
                    clean_title = re.sub('<.*?>', '', note['title'])
                    clean_content = re.sub('<.*?>', '', note['content'])
                    tool_result_text += f"- {clean_title}: {clean_content[:300]}...\n"
                tool_result_text += "]"
        
        # Detect MXH intent 
        elif any(kw in user_message.lower() for kw in ['mxh', 'facebook', 'tiktok', 'social']):
            result = AVAILABLE_TOOLS['get_all_mxh_cards']['function']()
            if result.get('success'):
                cards = result.get('cards', [])
                tool_result_text = f"\n\n[DANH SÁCH {len(cards)} THẺ MXH:\n"
                for card in cards[:10]:
                    tool_result_text += f"- {card['platform']}: {card['card_name']}\n"
                tool_result_text += "]"
        
        # Detect Telegram intent
        elif 'telegram' in user_message.lower():
            result = AVAILABLE_TOOLS['get_telegram_sessions']['function']()
            if result.get('success'):
                sessions = result.get('sessions', [])
                tool_result_text = f"\n\n[DANH SÁCH {len(sessions)} TELEGRAM SESSIONS:\n"
                for sess in sessions[:10]:
                    tool_result_text += f"- {sess['filename']}: {sess['status_text']} (Live: {sess['is_live']})\n"
                tool_result_text += "]"
        
        # Inject tool results into user message for AI to process
        if tool_result_text:
            user_message = user_message + tool_result_text
        
        # 3. Get History (Last 10 messages for context window)
        history_rows = conn.execute('SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT 10', (session_id,)).fetchall()
        history = [{'role': row['role'], 'content': row['content']} for row in reversed(history_rows)]
        conn.close()
        
        api_key = ''
        model_name = ''
        
        if provider == 'openai':
            api_key = settings.get('openai_api_key', '')
            # Use request model if provided, otherwise use settings, default to gpt-3.5-turbo
            model_name = (request_model if request_model else settings.get('openai_model', 'gpt-3.5-turbo')).strip()
        elif provider == 'gemini':
            api_key = settings.get('gemini_api_key', '')
            # Use request model if provided, otherwise use settings, default to gemini-2.5-flash
            model_name = (request_model if request_model else settings.get('gemini_model', 'gemini-2.5-flash')).strip()

        ai_response = ""

        # 4. Call AI Provider
        if not api_key:
             ai_response = f"Please configure your API Key for {provider} in Settings."
        elif provider == 'openai':
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                messages = [{'role': 'system', 'content': full_system_prompt}] + history
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages
                )
                ai_response = completion.choices[0].message.content
            except Exception as e:
                ai_response = f"OpenAI Error: {str(e)}"
                
        elif provider == 'gemini':
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                # Model mapping: auto-upgrade deprecated models to newer versions
                model_mapping = {
                    'gemini-pro': 'gemini-2.5-flash',
                    'gemini-1.5-pro': 'gemini-2.5-pro',
                    'gemini-1.5-flash': 'gemini-2.5-flash',
                    'gemini': 'gemini-2.5-flash',
                }
                
                # Default model if not specified
                if not model_name or model_name.strip() == '':
                    model_name = 'gemini-2.5-flash'
                
                # Clean up model name (remove extra spaces, lowercase)
                clean_model = model_name.strip().lower()
                
                # Auto-upgrade to newer model if using deprecated one
                if clean_model in model_mapping:
                    clean_model = model_mapping[clean_model]
                    print(f"INFO: Auto-upgraded '{model_name}' -> '{clean_model}'")
                
                # Remove 'models/' prefix if user added it (SDK adds it automatically)
                if clean_model.startswith('models/'):
                    clean_model = clean_model.replace('models/', '', 1)
                
                print(f"DEBUG: Using Gemini Model: '{clean_model}'") 
                
                model = genai.GenerativeModel(clean_model)
                
                # Construct prompt with history manually for stateless call
                prompt_parts = [full_system_prompt]
                for msg in history:
                    role_label = "User" if msg['role'] == 'user' else "Model"
                    prompt_parts.append(f"{role_label}: {msg['content']}")
                
                # The last message is already in history (user message), so we just generate

                response = model.generate_content("\n".join(prompt_parts))
                ai_response = response.text
            except Exception as e:
                ai_response = f"Gemini Error: {str(e)}"
        else:
            ai_response = f"Unknown provider: {provider}"

        # 5. Save AI Response
        conn = get_db_connection()
        conn.execute('INSERT INTO chat_history (role, content, timestamp, session_id) VALUES (?, ?, ?, ?)', 
                     ('assistant', ai_response, datetime.now().isoformat(), session_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'response': ai_response, 'session_id': session_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
