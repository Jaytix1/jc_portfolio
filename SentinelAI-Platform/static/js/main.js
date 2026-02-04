// ============================================
// SentinelAI Platform - Main JavaScript
// ============================================

// Configure marked for markdown rendering
marked.setOptions({
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true
});

// ============================================
// State Management
// ============================================

let currentModule = 'chat';
let conversations = [];
let activeConversationId = null;
let isGenerating = false;

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    checkOllamaStatus();
    loadConversations();
    setupCodeEditor();
    loadModels();

    // Auto-resize chat input
    const chatInput = document.getElementById('chat-input');
    chatInput.addEventListener('input', function() {
        autoResize(this);
    });
});

// ============================================
// Ollama Connection
// ============================================

async function checkOllamaStatus() {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');

    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        if (data.ollama_connected) {
            dot.className = 'status-dot connected';
            text.textContent = 'Connected';
        } else {
            dot.className = 'status-dot disconnected';
            text.textContent = 'Ollama offline';
        }
    } catch (error) {
        dot.className = 'status-dot disconnected';
        text.textContent = 'Server error';
    }
}

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        const select = document.getElementById('model-select');
        const settingsSelect = document.getElementById('settings-model');

        if (data.models && data.models.length > 0) {
            select.innerHTML = data.models.map(m =>
                `<option value="${m}">${m}</option>`
            ).join('');
            settingsSelect.innerHTML = select.innerHTML;
        }
    } catch (error) {
        console.error('Failed to load models:', error);
    }
}

// ============================================
// Module Switching
// ============================================

function switchModule(module) {
    currentModule = module;

    // Update tabs
    document.querySelectorAll('.module-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.module === module);
    });

    // Show/hide modules
    document.getElementById('chat-module').classList.toggle('hidden', module !== 'chat');
    document.getElementById('code-module').classList.toggle('hidden', module !== 'code');

    // Update label
    const labels = {
        'chat': 'General AI Chat',
        'code': 'Code Analysis'
    };
    document.getElementById('module-label').textContent = labels[module];
}

// ============================================
// Chat Functions
// ============================================

function getActiveConversation() {
    return conversations.find(c => c.id === activeConversationId);
}

function newConversation() {
    const conv = {
        id: Date.now(),
        title: 'New Chat',
        messages: [],
        createdAt: new Date().toISOString()
    };

    conversations.unshift(conv);
    activeConversationId = conv.id;
    saveConversations();
    renderConversationList();
    renderMessages();
}

function selectConversation(id) {
    activeConversationId = id;
    renderConversationList();
    renderMessages();
}

function deleteConversation(id, event) {
    event.stopPropagation();
    conversations = conversations.filter(c => c.id !== id);

    if (activeConversationId === id) {
        activeConversationId = conversations.length > 0 ? conversations[0].id : null;
    }

    saveConversations();
    renderConversationList();
    renderMessages();
}

function loadConversations() {
    const stored = localStorage.getItem('sentinelai_conversations');
    conversations = stored ? JSON.parse(stored) : [];

    if (conversations.length > 0) {
        activeConversationId = conversations[0].id;
    }

    renderConversationList();
    renderMessages();
}

function saveConversations() {
    // Keep only last 30 conversations
    if (conversations.length > 30) {
        conversations = conversations.slice(0, 30);
    }
    localStorage.setItem('sentinelai_conversations', JSON.stringify(conversations));
}

function renderConversationList() {
    const list = document.getElementById('conversation-list');

    if (conversations.length === 0) {
        list.innerHTML = `
            <div style="text-align: center; padding: 2rem 1rem; color: var(--text-muted); font-size: 0.85rem;">
                No conversations yet.<br>Start a new chat!
            </div>
        `;
        return;
    }

    list.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.id === activeConversationId ? 'active' : ''}"
             onclick="selectConversation(${conv.id})">
            <div class="conversation-item-title">${escapeHtml(conv.title)}</div>
            <div class="conversation-item-time">${getTimeAgo(new Date(conv.createdAt))}</div>
        </div>
    `).join('');
}

function renderMessages() {
    const container = document.getElementById('messages-container');
    const welcome = document.getElementById('welcome-screen');
    const conv = getActiveConversation();

    if (!conv || conv.messages.length === 0) {
        // Show welcome screen
        if (!welcome) {
            container.innerHTML = getWelcomeHTML();
        } else {
            welcome.style.display = 'flex';
        }
        // Remove any message elements
        container.querySelectorAll('.message').forEach(el => el.remove());
        return;
    }

    // Hide welcome screen
    if (welcome) welcome.style.display = 'none';

    // Remove existing messages (but not welcome screen)
    container.querySelectorAll('.message').forEach(el => el.remove());

    // Render messages
    conv.messages.forEach(msg => {
        const el = createMessageElement(msg.role, msg.content);
        container.appendChild(el);
    });

    scrollToBottom();
}

function createMessageElement(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avatarText = role === 'user' ? 'JC' : 'AI';

    div.innerHTML = `
        <div class="message-avatar">${avatarText}</div>
        <div class="message-content">${role === 'assistant' ? marked.parse(content) : escapeHtml(content).replace(/\n/g, '<br>')}</div>
    `;

    // Highlight code blocks
    if (role === 'assistant') {
        div.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
        });
    }

    return div;
}

function sendSuggestion(text) {
    document.getElementById('chat-input').value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message || isGenerating) return;

    // Create conversation if needed
    if (!activeConversationId) {
        newConversation();
    }

    const conv = getActiveConversation();

    // Add user message
    conv.messages.push({ role: 'user', content: message });

    // Update title from first message
    if (conv.messages.length === 1) {
        conv.title = message.substring(0, 50) + (message.length > 50 ? '...' : '');
        renderConversationList();
    }

    // Clear input
    input.value = '';
    autoResize(input);

    // Hide welcome, render messages
    const welcome = document.getElementById('welcome-screen');
    if (welcome) welcome.style.display = 'none';

    // Add user message to UI
    const container = document.getElementById('messages-container');
    container.appendChild(createMessageElement('user', message));

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typing-message';
    typingDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(typingDiv);
    scrollToBottom();

    // Disable send
    isGenerating = true;
    document.getElementById('send-btn').disabled = true;

    try {
        const model = document.getElementById('model-select').value;
        const persona = document.getElementById('persona-select').value;

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: conv.messages,
                model: model,
                persona: persona
            })
        });

        const data = await response.json();

        // Remove typing indicator
        const typingEl = document.getElementById('typing-message');
        if (typingEl) typingEl.remove();

        if (response.ok) {
            // Add assistant message
            conv.messages.push({ role: 'assistant', content: data.response });
            container.appendChild(createMessageElement('assistant', data.response));
        } else {
            container.appendChild(createErrorElement(data.error || 'Failed to get response'));
        }

        saveConversations();
    } catch (error) {
        const typingEl = document.getElementById('typing-message');
        if (typingEl) typingEl.remove();
        container.appendChild(createErrorElement('Failed to connect to server. Is it running?'));
    } finally {
        isGenerating = false;
        document.getElementById('send-btn').disabled = false;
        scrollToBottom();
    }
}

function createErrorElement(message) {
    const div = document.createElement('div');
    div.className = 'error-message';
    div.textContent = message;
    return div;
}

function handleChatKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

function scrollToBottom() {
    const container = document.getElementById('messages-container');
    container.scrollTop = container.scrollHeight;
}

// ============================================
// Code Module Functions
// ============================================

function setupCodeEditor() {
    const codeInput = document.getElementById('code-input');
    const charCount = document.getElementById('char-count');

    codeInput.addEventListener('input', function() {
        charCount.textContent = this.value.length.toLocaleString();
    });

    // Tab key support
    codeInput.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = start + 4;
        }
        if (e.ctrlKey && e.key === 'Enter') {
            analyzeCode();
        }
    });
}

async function analyzeCode() {
    const codeInput = document.getElementById('code-input');
    const language = document.getElementById('language-select').value;
    const results = document.getElementById('code-results');
    const btnText = document.getElementById('analyze-btn-text');
    const engineBadge = document.getElementById('engine-badge');
    const code = codeInput.value.trim();

    if (!code) {
        results.innerHTML = '<div class="error-message">Please enter some code to analyze.</div>';
        return;
    }

    // Show loading
    btnText.textContent = 'Analyzing...';
    results.innerHTML = `
        <div class="analyzing-spinner">
            <div class="spinner"></div>
            <p>SentinelCode is analyzing your code...</p>
        </div>
    `;

    try {
        const model = document.getElementById('model-select').value;
        const useClaude = document.getElementById('use-claude-toggle').checked;

        const response = await fetch('/api/code/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: language,
                model: model,
                use_claude: useClaude
            })
        });

        const data = await response.json();

        if (response.ok) {
            results.innerHTML = marked.parse(data.review);
            results.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
            engineBadge.textContent = data.engine;
            engineBadge.style.display = 'inline';
        } else {
            results.innerHTML = `<div class="error-message">${data.error}</div>`;
        }
    } catch (error) {
        results.innerHTML = '<div class="error-message">Failed to connect to server.</div>';
    } finally {
        btnText.textContent = 'Analyze';
    }
}

// ============================================
// Settings
// ============================================

function toggleSettings() {
    const overlay = document.getElementById('settings-overlay');
    overlay.classList.toggle('hidden');

    if (!overlay.classList.contains('hidden')) {
        refreshSettings();
    }
}

async function refreshSettings() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        document.getElementById('settings-ollama-status').textContent =
            data.ollama_connected ? 'Connected' : 'Disconnected';
        document.getElementById('settings-ollama-status').style.color =
            data.ollama_connected ? 'var(--accent-green)' : 'var(--accent-red)';

        document.getElementById('settings-models-list').textContent =
            data.models_available.length > 0
                ? data.models_available.join(', ')
                : 'No models installed';
    } catch (error) {
        document.getElementById('settings-ollama-status').textContent = 'Error';
    }
}

// ============================================
// Utility Functions
// ============================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

function getWelcomeHTML() {
    return `
        <div class="welcome-screen" id="welcome-screen">
            <svg class="welcome-logo" viewBox="0 0 40 40" width="80" height="80">
                <defs>
                    <linearGradient id="sg3" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#58a6ff"/>
                        <stop offset="100%" style="stop-color:#a371f7"/>
                    </linearGradient>
                    <linearGradient id="eg3" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#79b8ff"/>
                        <stop offset="100%" style="stop-color:#c4a5f9"/>
                    </linearGradient>
                </defs>
                <path d="M20 2 L36 8 L36 18 C36 28 28 36 20 38 C12 36 4 28 4 18 L4 8 Z" fill="url(#sg3)" opacity="0.9"/>
                <ellipse cx="20" cy="18" rx="8" ry="6" fill="#0d1117" opacity="0.8"/>
                <ellipse cx="20" cy="18" rx="6" ry="4.5" fill="none" stroke="url(#eg3)" stroke-width="1.5"/>
                <circle cx="20" cy="18" r="3" fill="url(#eg3)"/>
                <circle cx="21" cy="17" r="1" fill="white" opacity="0.8"/>
            </svg>
            <h2>SentinelAI</h2>
            <p>Self-hosted AI assistant powered by Ollama. Ask me anything.</p>
            <div class="welcome-prompts">
                <button class="prompt-suggestion" onclick="sendSuggestion('Explain how neural networks work')">
                    Explain neural networks
                </button>
                <button class="prompt-suggestion" onclick="sendSuggestion('Write a Python function to sort a list')">
                    Write a sorting function
                </button>
                <button class="prompt-suggestion" onclick="sendSuggestion('What are REST API best practices?')">
                    REST API best practices
                </button>
            </div>
        </div>
    `;
}
