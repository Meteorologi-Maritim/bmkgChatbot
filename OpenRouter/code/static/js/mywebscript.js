let activeChatMode = 'general';
let pdfChatHistory = [];
let activeFileNames = [];

document.addEventListener('DOMContentLoaded', () => {
    const homeScreen = document.getElementById('home-screen');
    const chatbotScreen = document.getElementById('chat-interface');
    const startChatBtn = document.getElementById('start-chat-btn');
    const sourceSelect = document.getElementById('source-select');
    const pdfFileInput = document.getElementById('pdf-file-input');
    const uploadStatusBar = document.getElementById('upload-status-bar');

    startChatBtn.addEventListener('click', () => {
        homeScreen.classList.add('hidden');
        chatbotScreen.classList.remove('hidden');
        appendMessage("Halo! Saya chatbot BMKG. Ada yang bisa saya bantu? ☁️", 'bot');
    });

    pdfFileInput.addEventListener('change', async(e) => {
        const files = Array.from(e.target.files);
        if (!files.length) return;

        activeFileNames = files.map(f => f.name).join(', ');
        document.getElementById('chatMessages').innerHTML = '';
        uploadStatusBar.textContent = `Memproses ${activeFileNames}...`;
        uploadStatusBar.style.display = 'block';
        uploadStatusBar.style.backgroundColor = '#005A9E';
        appendMessage("📂 Memproses dokumen Anda...", 'bot');

        const formData = new FormData();
        files.forEach(file => formData.append('pdf_file', file));

        try {
            const response = await fetch('/upload_pdf', { method: 'POST', body: formData });
            const data = await response.json();

            if (data.error) throw new Error(data.error);
            pdfChatHistory = data.initial_history || [];

            const firstReply = pdfChatHistory.find(msg => msg.role === 'assistant');
            if (firstReply) {
                appendMessage(formatSummary(firstReply.content), 'bot');
            } else {
                appendMessage("📄 Dokumen berhasil diproses. Silakan ajukan pertanyaan.", 'bot');
            }

            uploadStatusBar.textContent = `Mode Chat PDF Aktif: ${activeFileNames}`;
            sourceSelect.querySelector('option[value="pdf"]').disabled = false;
            sourceSelect.value = 'pdf';
            activeChatMode = 'pdf';

        } catch (err) {
            appendMessage(`❌ Gagal memproses PDF: ${err.message}`, 'bot');
            uploadStatusBar.textContent = 'Gagal mengunggah file.';
            uploadStatusBar.style.backgroundColor = '#dc3545';
            setTimeout(resetChatToGeneralMode, 3000);
        }
    });

    sourceSelect.addEventListener('change', (e) => {
        const value = e.target.value;

        if (value === 'general') {
            resetChatToGeneralMode();
        } else if (value === 'pdf') {
            if (activeFileNames) {
                activeChatMode = 'pdf';
                document.getElementById('chatMessages').innerHTML = '';
                appendMessage(`📄 Mode kembali ke chat PDF: ${activeFileNames}`, 'bot');
            } else {
                resetChatToGeneralMode();
            }
        } else if (value === 'web') {
            resetChatToWebMode();
        }
    });


    const inputField = document.getElementById('userInput');
    inputField.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendChat();
        }
    });
});

function resetChatToGeneralMode() {
    activeChatMode = 'general';
    activeFileNames = '';
    pdfChatHistory = [];

    const sourceSelect = document.getElementById('source-select');
    const uploadStatusBar = document.getElementById('upload-status-bar');
    sourceSelect.value = 'general';
    sourceSelect.querySelector('option[value="pdf"]').disabled = true;
    uploadStatusBar.style.display = 'none';

    document.getElementById('chatMessages').innerHTML = '';
    appendMessage('🌐 Mode diganti ke Pengetahuan Umum.', 'bot');
}

function resetChatToWebMode() {
    activeChatMode = 'web';
    activeFileNames = '';
    pdfChatHistory = [];

    const uploadStatusBar = document.getElementById('upload-status-bar');
    uploadStatusBar.style.display = 'none';

    document.getElementById('chatMessages').innerHTML = '';
    appendMessage('🌐 Mode diganti ke Pencarian Web. Gunakan kata kunci cuaca, maritim, atau BMKG.', 'bot');
}


async function sendChat() {
    const inputField = document.getElementById('userInput');
    const input = inputField.value.trim();
    if (!input) return;

    appendMessage(input, 'user');
    inputField.value = '';

    let endpoint = '';
    let payload = {};

    if (activeChatMode === 'pdf') {
        if (!pdfChatHistory.length) {
            appendMessage("📄 Silakan unggah file PDF terlebih dahulu.", 'bot');
            return;
        }

        endpoint = '/chat_pdf';
        pdfChatHistory.push({ role: 'user', content: input });
        payload = { history: pdfChatHistory, input: input };
    } else if (activeChatMode === 'web') {
        endpoint = '/chat';
        payload = { input: input, source: 'web' };
    } else {
        endpoint = '/chat';
        payload = { input: input, source: 'global' };
    }


    appendMessage('Memproses...', 'bot');

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        let reply = data.response || '❌ Terjadi kesalahan.';
        if (activeChatMode === 'pdf') {
            pdfChatHistory.push({ role: 'assistant', content: reply });
            reply = formatSummary(reply);
        }

        updateLastBotBubble(reply);
    } catch (err) {
        updateLastBotBubble(`❌ Gagal memproses permintaan: ${err.message}`);
    }
}

function appendMessage(text, sender) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${sender === 'user' ? 'user-message' : 'bot-message'}`;
    div.innerHTML = text.replace(/\n/g, '<br>');
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function updateLastBotBubble(newText) {
    const container = document.getElementById('chatMessages');
    const bubbles = container.getElementsByClassName('bot-message');
    const lastBubble = bubbles[bubbles.length - 1];
    if (lastBubble) {
        lastBubble.innerHTML = newText.replace(/\n/g, '<br>');
    }
}

function formatSummary(text) {
    const points = text.split(/\n\s*[*-]\s*/).filter(p => p.trim());
    let formatted = `<strong>📄 Ringkasan Dokumen:</strong><br>`;
    for (let point of points) {
        formatted += `• ${point.trim()}<br>`;
    }
    return formatted;
}