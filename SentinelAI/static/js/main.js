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

// State management
let uploadedFiles = [];
let activeFileIndex = -1;
let currentResult = null;

// Language detection mapping
const extensionToLanguage = {
    'py': 'python',
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'java': 'java',
    'cpp': 'cpp',
    'c': 'cpp',
    'cs': 'csharp',
    'go': 'go',
    'rs': 'rust',
    'php': 'php',
    'rb': 'ruby',
    'html': 'html',
    'css': 'css',
    'sql': 'sql',
    'vue': 'javascript',
    'swift': 'swift',
    'kt': 'kotlin',
    'scala': 'scala',
    'sh': 'bash',
    'bash': 'bash',
    'ps1': 'powershell',
    'json': 'json',
    'xml': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'md': 'markdown'
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    const codeInput = document.getElementById('code-input');
    const charCount = document.getElementById('char-count');
    const fileUploadZone = document.getElementById('file-upload-zone');
    const fileInput = document.getElementById('file-input');

    // Update character count
    function updateCharCount() {
        charCount.textContent = codeInput.value.length.toLocaleString();
    }

    codeInput.addEventListener('input', updateCharCount);
    updateCharCount();

    // Ctrl+Enter to submit
    codeInput.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            submitReview();
        }
    });

    // File upload handling
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    fileUploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadZone.classList.add('drag-over');
    });

    fileUploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        fileUploadZone.classList.remove('drag-over');
    });

    fileUploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUploadZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // Load history on start
    loadHistory();
});

// File handling functions
function handleFileSelect(e) {
    handleFiles(e.target.files);
}

async function handleFiles(files) {
    const fileArray = Array.from(files);

    for (const file of fileArray) {
        const content = await readFileContent(file);
        const extension = file.name.split('.').pop().toLowerCase();
        const language = extensionToLanguage[extension] || 'text';

        uploadedFiles.push({
            name: file.name,
            content: content,
            language: language,
            result: null
        });
    }

    renderFileTabs();

    // Select first file if none selected
    if (activeFileIndex === -1 && uploadedFiles.length > 0) {
        selectFile(0);
    }

    // Show analyze all button if multiple files
    const analyzeAllBtn = document.getElementById('analyze-all-btn');
    if (uploadedFiles.length > 1) {
        analyzeAllBtn.classList.remove('hidden');
    }
}

function readFileContent(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e);
        reader.readAsText(file);
    });
}

function renderFileTabs() {
    const tabsContainer = document.getElementById('file-tabs');

    if (uploadedFiles.length === 0) {
        tabsContainer.innerHTML = '';
        return;
    }

    tabsContainer.innerHTML = uploadedFiles.map((file, index) => `
        <div class="file-tab ${index === activeFileIndex ? 'active' : ''}" onclick="selectFile(${index})">
            <span class="file-tab-name">${file.name}</span>
            <button class="file-tab-close" onclick="event.stopPropagation(); removeFile(${index})">
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
            ${file.result ? '<span class="file-tab-analyzed"></span>' : ''}
        </div>
    `).join('');
}

function selectFile(index) {
    activeFileIndex = index;
    const file = uploadedFiles[index];

    // Update editor
    document.getElementById('code-input').value = file.content;
    document.getElementById('language').value = file.language;
    document.getElementById('char-count').textContent = file.content.length.toLocaleString();

    // Update results if available
    if (file.result) {
        displayResult(file.result);
    } else {
        resetResultsPanel();
    }

    renderFileTabs();
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);

    if (uploadedFiles.length === 0) {
        activeFileIndex = -1;
        document.getElementById('code-input').value = '';
        document.getElementById('char-count').textContent = '0';
        document.getElementById('analyze-all-btn').classList.add('hidden');
        resetResultsPanel();
    } else if (activeFileIndex >= uploadedFiles.length) {
        selectFile(uploadedFiles.length - 1);
    } else if (activeFileIndex === index) {
        selectFile(Math.max(0, index - 1));
    }

    renderFileTabs();

    if (uploadedFiles.length <= 1) {
        document.getElementById('analyze-all-btn').classList.add('hidden');
    }
}

function resetResultsPanel() {
    document.getElementById('review-output').innerHTML = `
        <div class="placeholder-state">
            <svg viewBox="0 0 80 80" class="placeholder-icon">
                <circle cx="40" cy="40" r="35" fill="none" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                <path d="M40 20 L40 45" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.3"/>
                <circle cx="40" cy="55" r="3" fill="currentColor" opacity="0.3"/>
            </svg>
            <p class="placeholder-title">Ready to Analyze</p>
            <p class="placeholder-text">Paste your code, upload files, or drag & drop to get detailed feedback on errors, security, and performance.</p>
        </div>
    `;
    document.getElementById('save-result-btn').classList.add('hidden');
    currentResult = null;
}

// Submit review
async function submitReview() {
    const codeInput = document.getElementById('code-input');
    const languageSelect = document.getElementById('language');
    const reviewOutput = document.getElementById('review-output');
    const reviewBtn = document.getElementById('review-btn');
    const btnText = reviewBtn.querySelector('.btn-text');
    const btnLoader = reviewBtn.querySelector('.btn-loader');
    const btnIcon = reviewBtn.querySelector('.btn-icon');

    const code = codeInput.value.trim();

    if (!code) {
        reviewOutput.innerHTML = '<div class="error-message">Please enter some code to analyze.</div>';
        return;
    }

    // Show loading state
    reviewBtn.disabled = true;
    btnText.textContent = 'Analyzing...';
    btnLoader.classList.remove('hidden');
    if (btnIcon) btnIcon.classList.add('hidden');

    reviewOutput.innerHTML = `
        <div class="placeholder-state">
            <div class="analyzing-animation">
                <svg viewBox="0 0 80 80" class="placeholder-icon spinning">
                    <circle cx="40" cy="40" r="35" fill="none" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                    <path d="M40 5 A35 35 0 0 1 75 40" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                </svg>
            </div>
            <p class="placeholder-title">Analyzing Code</p>
            <p class="placeholder-text">Checking for bugs, security issues, and performance optimizations...</p>
        </div>
    `;

    try {
        const response = await fetch('/review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                language: languageSelect.value
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentResult = {
                code: code,
                language: languageSelect.value,
                review: data.review,
                timestamp: new Date().toISOString(),
                fileName: activeFileIndex >= 0 ? uploadedFiles[activeFileIndex].name : null
            };

            // Store result in file if applicable
            if (activeFileIndex >= 0) {
                uploadedFiles[activeFileIndex].result = currentResult;
                renderFileTabs();
            }

            displayResult(currentResult);
            document.getElementById('save-result-btn').classList.remove('hidden');
        } else {
            reviewOutput.innerHTML = `<div class="error-message">${data.error || 'An error occurred while analyzing your code.'}</div>`;
        }
    } catch (error) {
        reviewOutput.innerHTML = `<div class="error-message">Failed to connect to the server. Please check your connection and try again.</div>`;
        console.error('Error:', error);
    } finally {
        // Reset button state
        reviewBtn.disabled = false;
        btnText.textContent = 'Analyze Code';
        btnLoader.classList.add('hidden');
        if (btnIcon) btnIcon.classList.remove('hidden');
    }
}

function displayResult(result) {
    const reviewOutput = document.getElementById('review-output');
    reviewOutput.innerHTML = marked.parse(result.review);
    reviewOutput.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
    document.getElementById('save-result-btn').classList.remove('hidden');
    currentResult = result;
}

// Analyze all files
async function analyzeAllFiles() {
    const analyzeAllBtn = document.getElementById('analyze-all-btn');
    const btnText = analyzeAllBtn.querySelector('.btn-text');

    analyzeAllBtn.disabled = true;

    for (let i = 0; i < uploadedFiles.length; i++) {
        const file = uploadedFiles[i];
        if (file.result) continue; // Skip already analyzed

        btnText.textContent = `Analyzing ${i + 1}/${uploadedFiles.length}...`;
        selectFile(i);

        await submitReview();

        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    btnText.textContent = 'Analyze All Files';
    analyzeAllBtn.disabled = false;
}

// History functions
function getHistory() {
    const history = localStorage.getItem('sentinelai_history');
    return history ? JSON.parse(history) : [];
}

function saveHistory(history) {
    localStorage.setItem('sentinelai_history', JSON.stringify(history));
    updateHistoryCount();
}

function saveCurrentResult() {
    if (!currentResult) return;

    const history = getHistory();
    const entry = {
        id: Date.now(),
        ...currentResult,
        savedAt: new Date().toISOString()
    };

    history.unshift(entry);

    // Keep only last 50 entries
    if (history.length > 50) {
        history.pop();
    }

    saveHistory(history);
    renderHistoryList();

    // Show feedback
    const saveBtn = document.getElementById('save-result-btn');
    const originalHTML = saveBtn.innerHTML;
    saveBtn.innerHTML = `
        <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
        </svg>
        Saved!
    `;
    saveBtn.classList.add('saved');

    setTimeout(() => {
        saveBtn.innerHTML = originalHTML;
        saveBtn.classList.remove('saved');
    }, 2000);
}

function loadHistory() {
    updateHistoryCount();
    renderHistoryList();
}

function updateHistoryCount() {
    const history = getHistory();
    document.getElementById('history-count').textContent = history.length;
}

function renderHistoryList() {
    const historyList = document.getElementById('history-list');
    const history = getHistory();

    if (history.length === 0) {
        historyList.innerHTML = `
            <div class="history-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p>No history yet</p>
                <span>Your analyses will appear here</span>
            </div>
        `;
        return;
    }

    historyList.innerHTML = history.map(entry => {
        const date = new Date(entry.savedAt);
        const timeAgo = getTimeAgo(date);
        const codePreview = entry.code.substring(0, 50).replace(/</g, '&lt;').replace(/>/g, '&gt;');

        return `
            <div class="history-item" onclick="loadHistoryEntry(${entry.id})">
                <div class="history-item-header">
                    <span class="history-item-lang">${entry.language}</span>
                    <span class="history-item-time">${timeAgo}</span>
                </div>
                ${entry.fileName ? `<div class="history-item-file">${entry.fileName}</div>` : ''}
                <div class="history-item-preview">${codePreview}${entry.code.length > 50 ? '...' : ''}</div>
                <button class="history-item-delete" onclick="event.stopPropagation(); deleteHistoryEntry(${entry.id})">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        `;
    }).join('');
}

function loadHistoryEntry(id) {
    const history = getHistory();
    const entry = history.find(e => e.id === id);

    if (!entry) return;

    // Clear uploaded files when loading from history
    uploadedFiles = [];
    activeFileIndex = -1;
    renderFileTabs();
    document.getElementById('analyze-all-btn').classList.add('hidden');

    // Load into editor
    document.getElementById('code-input').value = entry.code;
    document.getElementById('language').value = entry.language;
    document.getElementById('char-count').textContent = entry.code.length.toLocaleString();

    // Display result
    displayResult(entry);

    // Close history sidebar
    toggleHistory();
}

function deleteHistoryEntry(id) {
    const history = getHistory();
    const newHistory = history.filter(e => e.id !== id);
    saveHistory(newHistory);
    renderHistoryList();
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all history?')) {
        saveHistory([]);
        renderHistoryList();
    }
}

function toggleHistory() {
    const sidebar = document.getElementById('history-sidebar');
    sidebar.classList.toggle('open');
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

    return date.toLocaleDateString();
}
