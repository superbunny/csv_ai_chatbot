// Configuration
const API_BASE_URL = 'http://localhost:5001/api';

// DOM Elements
const homeScreen = document.getElementById('homeScreen');
const dashboardScreen = document.getElementById('dashboardScreen');
const uploadBtn = document.getElementById('uploadBtn');
const sendBtn = document.getElementById('sendBtn');
const searchInput = document.getElementById('searchInput');
const quickCards = document.querySelectorAll('.quick-card');

// Dashboard elements
const chatInput = document.querySelector('.chat-input');
const sendMessageBtn = document.querySelector('.send-message-btn');
const chatMessages = document.getElementById('chatMessages');
const dataTableBody = document.getElementById('dataTableBody');
const fileNameEl = document.querySelector('.file-name');
const fileSizeEl = document.querySelector('.file-size');
const statCards = document.querySelectorAll('.stat-value');
const panelDivider = document.getElementById('panelDivider');
const chatPanel = document.querySelector('.chat-panel');
const dataPanel = document.querySelector('.data-panel');

// State
let currentFile = null;
let isLoading = false;
let isDragging = false;

// Panel Resizing
if (panelDivider && chatPanel) {
    panelDivider.addEventListener('mousedown', (e) => {
        isDragging = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;

        const dashboardRect = dashboardScreen.getBoundingClientRect();
        const newWidth = e.clientX - dashboardRect.left;

        // Enforce min and max widths
        if (newWidth >= 300 && newWidth <= 600) {
            chatPanel.style.width = `${newWidth}px`;
        }
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}

// Screen Management
function showDashboard() {
    homeScreen.classList.add('hidden');
    dashboardScreen.classList.remove('hidden');
}

function showHome() {
    homeScreen.classList.remove('hidden');
    dashboardScreen.classList.add('hidden');
}

// Loading indicator
function setLoading(loading) {
    isLoading = loading;
    if (loading) {
        sendMessageBtn.disabled = true;
        sendMessageBtn.style.opacity = '0.5';
    } else {
        sendMessageBtn.disabled = false;
        sendMessageBtn.style.opacity = '1';
    }
}

// File Upload
uploadBtn.addEventListener('click', () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.csv';

    fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            await uploadFile(file);
        }
    });

    fileInput.click();
});

async function uploadFile(file) {
    try {
        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'include'  // Include cookies for session
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }

        currentFile = data;
        updateDashboardWithFileData(data);
        showDashboard();

        // Add welcome message to chat
        addAssistantMessage(`I've loaded <strong>${data.filename}</strong> with ${data.info.shape.rows} rows and ${data.info.shape.columns} columns. How can I help you analyze this data?`);

    } catch (error) {
        console.error('Upload error:', error);
        alert(`Upload failed: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

function updateDashboardWithFileData(fileData) {
    const info = fileData.info;
    const preview = fileData.preview;

    // Update file info
    fileNameEl.textContent = fileData.filename;
    fileSizeEl.textContent = `${info.memory_usage_mb.toFixed(2)} MB`;

    // Update stats
    const statValues = document.querySelectorAll('.stat-value');
    statValues[0].textContent = info.shape.rows.toLocaleString();
    statValues[1].textContent = info.shape.columns;
    statValues[2].textContent = `${info.total_missing} (${(info.total_missing / (info.shape.rows * info.shape.columns) * 100).toFixed(1)}%)`;
    statValues[3].textContent = `${info.memory_usage_mb.toFixed(1)} MB`;

    // Update data table
    if (preview && preview.columns && preview.rows) {
        // Update table headers
        const tableHead = document.querySelector('.data-table thead tr');
        tableHead.innerHTML = '';
        preview.columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            tableHead.appendChild(th);
        });

        // Update table body
        dataTableBody.innerHTML = '';
        preview.rows.forEach(row => {
            const tr = document.createElement('tr');
            preview.columns.forEach(col => {
                const td = document.createElement('td');
                const value = row[col];

                // Format the value
                if (value === null || value === undefined) {
                    td.textContent = '—';
                    td.style.color = 'var(--text-muted)';
                } else {
                    td.textContent = value;
                }

                tr.appendChild(td);
            });
            dataTableBody.appendChild(tr);
        });

        // Update row count
        const rowCountEl = document.querySelector('.row-count');
        if (rowCountEl) {
            rowCountEl.textContent = `Showing ${preview.rows.length} of ${info.shape.rows.toLocaleString()} rows`;
        }
    }
}

// Chat Functions
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addAssistantMessage(html, visualizations = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';

    let content = `<div class="message-content">${html}</div>`;

    // Add visualizations if any
    if (visualizations && visualizations.length > 0) {
        visualizations.forEach(vizUrl => {
            content += `<div class="viz-container"><img src="${API_BASE_URL}${vizUrl}" style="max-width: 100%; border-radius: 8px; margin-top: 12px;" /></div>`;
        });
    }

    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message loading-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading-dots">
                <span>.</span><span>.</span><span>.</span>
            </div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}

function removeLoadingMessage() {
    const loadingMsg = document.querySelector('.loading-message');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

async function sendChatMessage(message) {
    if (!message.trim() || isLoading) return;

    try {
        setLoading(true);
        addUserMessage(message);
        const loadingMsg = addLoadingMessage();

        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        removeLoadingMessage();

        if (!response.ok) {
            throw new Error(data.error || 'Chat request failed');
        }

        // Format the assistant's response
        let formattedMessage = formatMarkdown(data.message);

        // Add assistant message with visualizations
        addAssistantMessage(formattedMessage, data.visualizations);

    } catch (error) {
        console.error('Chat error:', error);
        removeLoadingMessage();
        addAssistantMessage(`<p style="color: #EF4444;">Error: ${error.message}</p>`);
    } finally {
        setLoading(false);
    }
}

// Format markdown-like text to HTML
function formatMarkdown(text) {
    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Lists
    text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    // Line breaks
    text = text.replace(/\n\n/g, '</p><p>');
    text = '<p>' + text + '</p>';
    return text;
}

// Event Listeners - Send message
sendMessageBtn.addEventListener('click', () => {
    const message = chatInput.value.trim();
    if (message) {
        sendChatMessage(message);
        chatInput.value = '';
    }
});

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessageBtn.click();
    }
});

// Quick start cards
quickCards.forEach(card => {
    card.addEventListener('click', () => {
        const prompt = card.getAttribute('data-prompt');
        searchInput.value = prompt;
        // Don't auto-navigate, let user upload first
        if (currentFile) {
            showDashboard();
            setTimeout(() => {
                chatInput.value = prompt;
                sendChatMessage(prompt);
                chatInput.value = '';
            }, 500);
        }
    });
});

// Clear chat functionality
const clearChatBtn = document.querySelector('.text-btn:not(.primary)');
if (clearChatBtn) {
    clearChatBtn.addEventListener('click', () => {
        // Clear all messages
        chatMessages.innerHTML = '';
    });
}

// New chat functionality
const newChatBtn = document.querySelector('.text-btn.primary');
if (newChatBtn) {
    newChatBtn.addEventListener('click', async () => {
        // Clear session
        try {
            await fetch(`${API_BASE_URL}/session/clear`, {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Error clearing session:', error);
        }

        currentFile = null;
        showHome();
        searchInput.value = '';

        // Clear chat messages
        chatMessages.innerHTML = '';
    });
}

// Export functionality
const exportBtn = document.querySelector('.export-btn');
if (exportBtn) {
    exportBtn.addEventListener('click', () => {
        console.log('Exporting report...');
        const originalText = exportBtn.innerHTML;
        exportBtn.innerHTML = '<span class="material-icons">check_circle</span>Exported!';
        exportBtn.style.background = 'var(--status-green)';

        setTimeout(() => {
            exportBtn.innerHTML = originalText;
            exportBtn.style.background = '';
        }, 2000);
    });
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
console.log('CSV Chatbot initialized');
console.log('Backend API:', API_BASE_URL);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape key to go back to home (if no file uploaded)
    if (e.key === 'Escape' && !dashboardScreen.classList.contains('hidden') && !currentFile) {
        showHome();
    }
});

// Add loading animation CSS dynamically
const style = document.createElement('style');
style.textContent = `
    .loading-dots {
        display: inline-block;
    }
    .loading-dots span {
        animation: blink 1.4s infinite both;
        font-size: 2rem;
        line-height: 1;
    }
    .loading-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .loading-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes blink {
        0%, 80%, 100% {
            opacity: 0;
        }
        40% {
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
