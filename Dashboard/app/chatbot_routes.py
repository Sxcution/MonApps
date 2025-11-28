from flask import Blueprint, request, jsonify, render_template
import sqlite3
import json
import os
import uuid
from datetime import datetime
from .database import get_db_connection

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
        provider = settings.get('provider', 'openai')
        system_prompt = settings.get('system_prompt', 'You are a helpful Dashboard Assistant.')
        
        api_key = ''
        model_name = ''
        
        if provider == 'openai':
            api_key = settings.get('openai_api_key', '')
            model_name = settings.get('openai_model', 'gpt-3.5-turbo').strip()
        elif provider == 'gemini':
            api_key = settings.get('gemini_api_key', '')
            model_name = settings.get('gemini_model', 'gemini-pro').strip()
        
        context = get_context_data()
        full_system_prompt = f"{system_prompt}\n\nCURRENT DASHBOARD CONTEXT:\n{context}"
        
        # 3. Get History (Last 10 messages for context window)
        history_rows = conn.execute('SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT 10', (session_id,)).fetchall()
        history = [{'role': row['role'], 'content': row['content']} for row in reversed(history_rows)]
        conn.close()

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
                
                # Sanitize model name for Gemini (e.g. ensure no spaces, maybe add 'models/' if needed but usually not)
                # Common error is "unexpected model name format" if it has spaces or invalid chars
                print(f"DEBUG: Using Gemini Model: '{model_name}'") 
                
                model = genai.GenerativeModel(model_name)
                
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
