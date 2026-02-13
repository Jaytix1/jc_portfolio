// FlakkOps - Main JavaScript

// ============================================
// File Upload
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('manifest-file');
    const fileName = document.getElementById('file-name');

    // File input display
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileName.textContent = this.files[0].name;
            } else {
                fileName.textContent = 'Choose file or drag here';
            }
        });
    }

    // Upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const statusDiv = document.getElementById('upload-status');

            statusDiv.className = 'upload-status loading';
            statusDiv.innerHTML = '<div class="spinner"></div> Processing manifest...';
            statusDiv.classList.remove('hidden');

            try {
                const response = await fetch('/api/manifest/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    statusDiv.className = 'upload-status success';
                    statusDiv.innerHTML = `
                        <strong>Success!</strong> Manifest processed.<br>
                        ${result.items_found} items found, ${result.new_products} new products detected.
                        <br><br>
                        <a href="/manifest/${result.manifest_id}" class="btn btn-primary btn-sm">View Manifest</a>
                    `;

                    // Reset form
                    uploadForm.reset();
                    fileName.textContent = 'Choose file or drag here';

                    // Reload page after delay to show in list
                    setTimeout(() => {
                        window.location.href = `/manifest/${result.manifest_id}`;
                    }, 2000);
                } else {
                    statusDiv.className = 'upload-status error';
                    statusDiv.innerHTML = `<strong>Error:</strong> ${result.error}`;
                }
            } catch (error) {
                statusDiv.className = 'upload-status error';
                statusDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
            }
        });
    }
});


// ============================================
// Tasks
// ============================================

async function completeTask(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'completed' })
        });

        if (response.ok) {
            const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskElement) {
                taskElement.style.opacity = '0.5';
                taskElement.style.textDecoration = 'line-through';
                setTimeout(() => taskElement.remove(), 500);
            }
        }
    } catch (error) {
        console.error('Error completing task:', error);
    }
}

async function updateTaskStatus(taskId, status) {
    try {
        const response = await fetch(`/api/task/${taskId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            window.location.reload();
        }
    } catch (error) {
        console.error('Error updating task:', error);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
        const response = await fetch(`/api/task/${taskId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskElement) {
                taskElement.style.opacity = '0';
                setTimeout(() => taskElement.remove(), 300);
            }
        }
    } catch (error) {
        console.error('Error deleting task:', error);
    }
}

function showNewTaskModal() {
    document.getElementById('task-modal').classList.remove('hidden');
}

function closeTaskModal() {
    document.getElementById('task-modal').classList.add('hidden');
    document.getElementById('task-form').reset();
}

async function createTask(e) {
    e.preventDefault();

    const form = e.target;
    const data = {
        title: form.title.value,
        description: form.description.value,
        priority: form.priority.value,
        due_date: form.due_date.value || null
    };

    try {
        const response = await fetch('/api/task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeTaskModal();
            window.location.reload();
        }
    } catch (error) {
        console.error('Error creating task:', error);
    }
}


// ============================================
// Search / Filter
// ============================================

function filterItems() {
    const searchValue = document.getElementById('item-search').value.toLowerCase();
    const table = document.getElementById('items-table');
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchValue) ? '' : 'none';
    });
}

function filterProducts() {
    const searchValue = document.getElementById('product-search').value.toLowerCase();
    const table = document.getElementById('products-table');
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchValue) ? '' : 'none';
    });
}


// ============================================
// AI Analysis
// ============================================

async function analyzeManifest(manifestId) {
    const resultDiv = document.getElementById('analysis-result');
    const contentDiv = resultDiv.querySelector('.analysis-content');

    resultDiv.classList.remove('hidden');
    contentDiv.innerHTML = '<div class="spinner"></div> Analyzing manifest with AI...';

    try {
        const response = await fetch(`/api/manifest/${manifestId}/analyze`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.analysis) {
            contentDiv.innerHTML = formatMarkdown(result.analysis);
        } else {
            contentDiv.innerHTML = `<span style="color: var(--accent-red)">Error: ${result.error}</span>`;
        }
    } catch (error) {
        contentDiv.innerHTML = `<span style="color: var(--accent-red)">Error: ${error.message}</span>`;
    }
}


// ============================================
// AI Chat
// ============================================

async function sendMessage(e) {
    e.preventDefault();

    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const messagesContainer = document.getElementById('chat-messages');

    // Add user message
    messagesContainer.innerHTML += `
        <div class="message user">
            <div class="message-avatar">U</div>
            <div class="message-content">${escapeHtml(message)}</div>
        </div>
    `;

    input.value = '';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    messagesContainer.innerHTML += `
        <div class="message assistant" id="${loadingId}">
            <div class="message-avatar">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                    <rect width="32" height="32" rx="8" fill="url(#ai-gradient-${loadingId})"/>
                    <circle cx="16" cy="16" r="8" stroke="white" stroke-width="2" fill="none"/>
                    <circle cx="16" cy="16" r="3" fill="white"/>
                    <defs>
                        <linearGradient id="ai-gradient-${loadingId}" x1="0" y1="0" x2="32" y2="32">
                            <stop offset="0%" stop-color="#0066FF"/>
                            <stop offset="100%" stop-color="#00D4FF"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <div class="message-content">
                <div class="spinner"></div>
            </div>
        </div>
    `;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        const response = await fetch('/api/assistant/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const result = await response.json();
        const loadingElement = document.getElementById(loadingId);

        if (result.response) {
            loadingElement.querySelector('.message-content').innerHTML = formatMarkdown(result.response);
        } else {
            loadingElement.querySelector('.message-content').innerHTML =
                `<span style="color: var(--accent-red)">Error: ${result.error}</span>`;
        }
    } catch (error) {
        const loadingElement = document.getElementById(loadingId);
        loadingElement.querySelector('.message-content').innerHTML =
            `<span style="color: var(--accent-red)">Error: ${error.message}</span>`;
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function askQuestion(question) {
    document.getElementById('chat-input').value = question;
    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
}


// ============================================
// Utilities
// ============================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    // Basic markdown-like formatting
    return text
        // Headers
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Lists
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}


// ============================================
// Keyboard Shortcuts
// ============================================

document.addEventListener('keydown', function(e) {
    // Escape to close modal
    if (e.key === 'Escape') {
        const modal = document.getElementById('task-modal');
        if (modal && !modal.classList.contains('hidden')) {
            closeTaskModal();
        }
    }
});
