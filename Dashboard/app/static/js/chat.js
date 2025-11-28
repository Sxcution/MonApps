let currentSessionId = null;
let providerSettings = {}; // Store settings for all providers

document.addEventListener('DOMContentLoaded', function () {
    loadSessions();
    loadAISettings();

    // Auto-resize textarea
    const textarea = document.getElementById('user-input');
    textarea.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = '24px'; // Reset to min height
    });

    // Handle Enter key to send
    textarea.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Handle Form Submit
    document.getElementById('chat-form').addEventListener('submit', function (e) {
        e.preventDefault();
        sendMessage();
    });

    // Search filter
    document.getElementById('chatSearch').addEventListener('input', function (e) {
        const term = e.target.value.toLowerCase();
        const items = document.querySelectorAll('.chat-history-item');
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(term) ? 'block' : 'none';
        });
    });

    // Provider Change Listener
    document.getElementById('ai-provider').addEventListener('change', function (e) {
        updateSettingsUI(e.target.value);
    });
});

function toggleSidebar() {
    document.getElementById('chatSidebar').classList.toggle('show');
}

async function loadSessions() {
    try {
        const response = await fetch('/api/chat/sessions');
        const data = await response.json();
        const list = document.getElementById('chatHistoryList');
        list.innerHTML = '';

        if (data.success && data.sessions.length > 0) {
            data.sessions.forEach(session => {
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'chat-history-item';
                item.textContent = session.title || 'New Chat';
                item.dataset.id = session.id;
                item.onclick = (e) => {
                    e.preventDefault();
                    loadSession(session.id);
                };
                list.appendChild(item);
            });
        } else {
            list.innerHTML = '<div class="text-center text-muted small mt-3">No history</div>';
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

function startNewChat() {
    currentSessionId = null;
    document.getElementById('chat-messages').innerHTML = `
        <div class="h-100 d-flex flex-column justify-content-center align-items-center text-center p-4 empty-state">
            <div class="mb-4">
                <div class="logo-circle">
                    <i class="bi bi-robot fs-1"></i>
                </div>
            </div>
            <h3 class="mb-3 fw-bold">What's on your mind today?</h3>
            <div class="d-flex flex-wrap justify-content-center gap-2" id="suggestion-chips">
                <button class="btn btn-suggestion" onclick="sendSuggestion('Check my recent notes')">Check my recent notes</button>
                <button class="btn btn-suggestion" onclick="sendSuggestion('Analyze Telegram sessions')">Analyze Telegram sessions</button>
                <button class="btn btn-suggestion" onclick="sendSuggestion('List my social accounts')">List my social accounts</button>
            </div>
        </div>
    `;
    document.querySelectorAll('.chat-history-item').forEach(el => el.classList.remove('active'));
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    document.querySelectorAll('.chat-history-item').forEach(el => {
        el.classList.toggle('active', el.dataset.id === sessionId);
    });

    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '<div class="text-center mt-5"><div class="spinner-border text-light" role="status"></div></div>';

    try {
        const response = await fetch(`/api/chat/history/${sessionId}`);
        const data = await response.json();
        chatMessages.innerHTML = '';
        if (data.success) {
            data.history.forEach(msg => appendMessage(msg.role, msg.content));
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    } catch (error) {
        chatMessages.innerHTML = `<div class="text-danger text-center mt-5">Error loading chat: ${error.message}</div>`;
    }
}

function appendMessage(role, content, modelName = null) {
    const chatMessages = document.getElementById('chat-messages');
    const emptyState = chatMessages.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const messageRow = document.createElement('div');
    messageRow.className = `message-row ${role === 'user' ? 'user' : 'ai'}`; // Add specific class

    const avatarClass = role === 'user' ? 'user-avatar-img' : 'ai-avatar-img';
    const avatarIcon = role === 'user' ? '<i class="bi bi-person"></i>' : '<i class="bi bi-robot"></i>';

    // Determine Display Name
    let displayName = 'ChatGPT'; // Default fallback
    if (role === 'user') {
        displayName = 'You';
    } else {
        // Use passed model name, or current setting, or fallback
        if (modelName) {
            displayName = modelName;
        } else {
            // Try to get from settings if not passed (e.g. history load)
            // Note: History doesn't save model name per msg yet, so this might be generic on reload
            // For now, use the current provider's model setting as a best guess for history
            const provider = providerSettings.provider || 'openai';
            if (provider === 'openai') displayName = providerSettings.openai_model || 'GPT-3.5 Turbo';
            else if (provider === 'gemini') displayName = providerSettings.gemini_model || 'Gemini Pro';
        }
    }

    let formattedContent = content
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    messageRow.innerHTML = `
        <div class="message-container">
            <div class="message-avatar ${avatarClass}">${avatarIcon}</div>
            <div class="message-content">
                <div class="fw-bold mb-1">${displayName}</div>
                <div>${formattedContent}</div>
            </div>
        </div>
    `;
    chatMessages.appendChild(messageRow);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendSuggestion(text) {
    document.getElementById('user-input').value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();

    if (!message) return;

    input.value = '';
    input.style.height = '24px';

    appendMessage('user', message);

    const chatMessages = document.getElementById('chat-messages');
    const loadingId = 'loading-' + Date.now();
    const loadingRow = document.createElement('div');
    loadingRow.className = 'message-row ai'; // Add ai class
    loadingRow.id = loadingId;

    // Get current model name for loading state
    let currentModelName = 'ChatGPT';
    const provider = providerSettings.provider || 'openai';
    if (provider === 'openai') currentModelName = providerSettings.openai_model || 'GPT-3.5 Turbo';
    else if (provider === 'gemini') currentModelName = providerSettings.gemini_model || 'Gemini Pro';

    loadingRow.innerHTML = `
        <div class="message-container">
            <div class="message-avatar ai-avatar-img"><i class="bi bi-robot"></i></div>
            <div class="message-content">
                <div class="fw-bold mb-1">${currentModelName}</div>
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(loadingRow);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: currentSessionId })
        });
        const data = await response.json();
        document.getElementById(loadingId).remove();

        if (data.success) {
            if (!currentSessionId || currentSessionId !== data.session_id) {
                currentSessionId = data.session_id;
                loadSessions();
            }
            // Pass the model name used (we assume it's the same as what we sent)
            appendMessage('assistant', data.response, currentModelName);
        } else {
            appendMessage('assistant', 'Error: ' + data.error, currentModelName);
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        appendMessage('assistant', 'Network Error: ' + error.message, currentModelName);
    } finally {
        sendBtn.disabled = false;
    }
}

async function clearAllChats() {
    if (!confirm('Are you sure you want to delete all chat history?')) return;
    alert('Feature coming soon!');
}

// --- Smart Settings Logic ---

async function loadAISettings() {
    try {
        const response = await fetch('/api/chat/settings');
        const data = await response.json();
        if (data.success) {
            providerSettings = data.settings; // Store all settings

            // Set current provider (default to openai if not set)
            const currentProvider = providerSettings.provider || 'openai';
            document.getElementById('ai-provider').value = currentProvider;
            document.getElementById('ai-system-prompt').value = providerSettings.system_prompt || 'You are a helpful Dashboard Assistant.';

            updateSettingsUI(currentProvider);
            updateHeaderModelName(currentProvider);
        }
    } catch (error) { console.error(error); }
}

function updateSettingsUI(provider) {
    // Load Key/Model based on provider
    const apiKeyInput = document.getElementById('ai-api-key');
    const modelInput = document.getElementById('ai-model');

    if (provider === 'openai') {
        apiKeyInput.value = providerSettings.openai_api_key || '';
        modelInput.value = providerSettings.openai_model || 'gpt-3.5-turbo';
        modelInput.placeholder = 'e.g. gpt-4o';
    } else if (provider === 'gemini') {
        apiKeyInput.value = providerSettings.gemini_api_key || '';
        modelInput.value = providerSettings.gemini_model || 'gemini-pro';
        modelInput.placeholder = 'e.g. gemini-1.5-pro';
    }
}

function updateHeaderModelName(provider) {
    const modelNameEl = document.getElementById('current-model-name');
    let modelName = '';

    if (provider === 'openai') {
        modelName = providerSettings.openai_model || 'GPT-3.5 Turbo';
    } else if (provider === 'gemini') {
        modelName = providerSettings.gemini_model || 'Gemini Pro';
    }

    // Capitalize provider name for display if model is empty/default
    if (!modelName) modelName = provider.charAt(0).toUpperCase() + provider.slice(1);

    modelNameEl.textContent = modelName;
}

async function saveAISettings() {
    const provider = document.getElementById('ai-provider').value;
    const apiKey = document.getElementById('ai-api-key').value;
    const model = document.getElementById('ai-model').value;
    const systemPrompt = document.getElementById('ai-system-prompt').value;

    // Update local state
    providerSettings.provider = provider;
    providerSettings.system_prompt = systemPrompt;

    if (provider === 'openai') {
        providerSettings.openai_api_key = apiKey;
        providerSettings.openai_model = model;
    } else if (provider === 'gemini') {
        providerSettings.gemini_api_key = apiKey;
        providerSettings.gemini_model = model;
    }

    try {
        const response = await fetch('/api/chat/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(providerSettings) // Send all settings
        });
        const data = await response.json();
        if (data.success) {
            alert('Settings saved!');
            updateHeaderModelName(provider);
            const modal = bootstrap.Modal.getInstance(document.getElementById('aiSettingsModal'));
            modal.hide();
        } else { alert('Error: ' + data.error); }
    } catch (error) { alert('Error: ' + error.message); }
}
