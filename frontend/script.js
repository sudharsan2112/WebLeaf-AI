const API_BASE = window.location.origin;

let currentUrl = localStorage.getItem('current_kb_url') || "";
let kbId = localStorage.getItem('current_kb_id');
let sessionId = localStorage.getItem('chat_session_id') || ('session_' + Math.random().toString(36).substr(2, 9));
localStorage.setItem('chat_session_id', sessionId);

let pollingInterval = null;

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    // Setup Marked.js
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            highlight: function(code, lang) {
                if (typeof hljs !== 'undefined') {
                    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                    return hljs.highlight(code, { language }).value;
                }
                return code;
            }
        });
    }

    const urlParams = new URLSearchParams(window.location.search);
    const paramKbId = urlParams.get('kb_id');
    if (paramKbId) {
        kbId = paramKbId;
        localStorage.setItem('current_kb_id', kbId);
        showDashboard();
    }
});

function setTreeStage(i) {
    document.querySelectorAll(".tstage").forEach((g, idx) => {
        g.classList.toggle("active", idx === i);
    });
    document.querySelectorAll(".stage-dot").forEach((d, idx) => {
        d.classList.toggle("active", idx === i);
        d.classList.toggle("done", idx < i);
    });
}

async function startCrawl() {
    const input = document.getElementById("url");
    if (!input) return;
    
    const urlVal = input.value.trim();
    if (!urlVal) {
        alert("Please enter a website URL.");
        input.focus();
        return;
    }

    try {
        new URL(urlVal);
    } catch {
        alert("Invalid URL format. Please include http:// or https://");
        input.focus();
        return;
    }

    currentUrl = urlVal;
    localStorage.setItem('current_kb_url', currentUrl);

    document.getElementById("crawlArea").classList.add("show");
    input.disabled = true;
    
    const btn = document.querySelector(".url-button");
    if (btn) btn.disabled = true;

    document.getElementById("growthRing").classList.add("run");
    document.getElementById("spores").classList.add("run");

    setTreeStage(0);

    try {
        const response = await fetch(`${API_BASE}/crawl`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: urlVal})
        });

        if (!response.ok) throw new Error("Crawl request failed");

        const data = await response.json();
        kbId = data.kb_id;
        localStorage.setItem('current_kb_id', kbId);

        pollStatus();
    } catch (e) {
        alert("Error connecting to server. Is the backend running?");
        input.disabled = false;
        if (btn) btn.disabled = false;
        document.getElementById("crawlArea").classList.remove("show");
    }
}

async function pollStatus() {
    if (pollingInterval) clearInterval(pollingInterval);

    const stepIds = ["step1", "step2", "step3", "step4", "step5"];
    const messages = [
        "🌱 Planting the seed — discovering pages...",
        "🌿 Sprouting — following links...",
        "🌱 Growing roots — extracting content...",
        "🌳 Growing branches — creating embeddings...",
        "🌳 Growing the knowledge tree — building knowledge base...",
        "✓ Knowledge tree fully grown — knowledge base ready!"
    ];

    const statusEl = document.getElementById("crawlStatus");
    if (statusEl) statusEl.textContent = messages[0];

    pollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/status?kb_id=${kbId}`);
            if (!res.ok) return;

            const data = await res.json();
            
            // Update stats elements if present
            const pagesEl = document.getElementById("pages");
            if (pagesEl) pagesEl.innerText = data.pages_crawled || 0;
            
            const chunksEl = document.getElementById("chunks");
            if (chunksEl) chunksEl.innerText = data.chunks_created || 0;

            if (data.status === 'completed') {
                clearInterval(pollingInterval);
                setTreeStage(5);

                // Mark all steps done
                stepIds.forEach(id => {
                    const step = document.getElementById(id);
                    if (step) {
                        step.classList.remove("active");
                        step.classList.add("done");
                    }
                });

                document.getElementById("growthRing").classList.remove("run");
                document.getElementById("spores").classList.remove("run");
                if (statusEl) statusEl.textContent = messages[5];

                setTimeout(showDashboard, 1000);

            } else if (data.status === 'error') {
                clearInterval(pollingInterval);
                if (statusEl) statusEl.textContent = `Error: ${data.error || 'Crawl failed'}`;
                const input = document.getElementById("url");
                if (input) input.disabled = false;
                const btn = document.querySelector(".url-button");
                if (btn) btn.disabled = false;

            } else {
                // Progressive stage calculation (0 to 4)
                const pages = data.pages_crawled || 0;
                const chunks = data.chunks_created || 0;
                let current = Math.min(4, Math.floor((pages / 10) * 4) + (chunks > 0 ? 1 : 0));
                
                setTreeStage(current);
                if (statusEl) statusEl.textContent = messages[current];

                stepIds.forEach((id, idx) => {
                    const step = document.getElementById(id);
                    if (step) {
                        step.classList.toggle("active", idx === current);
                        step.classList.toggle("done", idx < current);
                    }
                });
            }

        } catch (e) {
            console.error("Polling error", e);
        }
    }, 1500);
}

async function showDashboard() {
    const page1 = document.getElementById("page1");
    const page2 = document.getElementById("page2");
    if (page1 && page2) {
        page1.classList.remove("active");
        page2.classList.add("active");
    }

    const finalUrlEl = document.getElementById("finalUrl");
    if (finalUrlEl) finalUrlEl.textContent = currentUrl || localStorage.getItem('current_kb_url') || `KB ID: ${kbId}`;

    // Fetch status info for sidebar stats
    try {
        const res = await fetch(`${API_BASE}/status?kb_id=${kbId}`);
        if (res.ok) {
            const data = await res.json();
            const pagesEl = document.getElementById("pages");
            if (pagesEl) pagesEl.innerText = data.pages_crawled || 0;
            const chunksEl = document.getElementById("chunks");
            if (chunksEl) chunksEl.innerText = data.chunks_created || 0;
        }
    } catch (e) {
        console.error("Error updating dashboard stats", e);
    }

    // Load Chat History
    try {
        const res = await fetch(`${API_BASE}/history?session_id=${sessionId}`);
        if (res.ok) {
            const data = await res.json();
            if (data.history && data.history.length > 0) {
                const box = document.getElementById("messages");
                if (box) {
                    box.innerHTML = `
                        <div class="msg ai">
                          Hello! 🌿 I'm your Web Assistant.
                          <br><br>
                          I've finished reading the website. Ask me anything about its content and I'll search the knowledge base for the answer.
                        </div>
                    `;
                    data.history.forEach(msg => appendMessage(msg.role, msg.content));
                }
            }
        }
    } catch (e) {
        console.error("Error loading chat history", e);
    }
}

function goBack() {
    const page1 = document.getElementById("page1");
    const page2 = document.getElementById("page2");
    if (page1 && page2) {
        page2.classList.remove("active");
        page1.classList.add("active");
    }

    const input = document.getElementById("url");
    if (input) input.disabled = false;
    
    const btn = document.querySelector(".url-button");
    if (btn) btn.disabled = false;

    const crawlArea = document.getElementById("crawlArea");
    if (crawlArea) crawlArea.classList.remove("show");
    
    document.getElementById("growthRing").classList.remove("run");
    document.getElementById("spores").classList.remove("run");

    const stepIds = ["step1", "step2", "step3", "step4", "step5"];
    stepIds.forEach((id, i) => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove("active", "done");
            if (i === 0) el.classList.add("active");
        }
    });

    const statusEl = document.getElementById("crawlStatus");
    if (statusEl) statusEl.textContent = "🌱 Planting the seed — discovering pages...";
    
    setTreeStage(0);
}

function appendMessage(role, content) {
    const box = document.getElementById("messages");
    if (!box) return null;

    const msgDiv = document.createElement("div");
    msgDiv.className = `msg ${role === 'assistant' || role === 'ai' ? 'ai' : 'user'}`;
    
    if (role === 'assistant' || role === 'ai') {
        msgDiv.innerHTML = typeof marked !== 'undefined' ? marked.parse(content) : escapeHtml(content);
        addCopyButtons(msgDiv);
    } else {
        msgDiv.innerText = content;
    }

    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
    return msgDiv;
}

function renderSources(sources, msgDiv) {
    if (!sources || sources.length === 0 || !msgDiv) return;

    sources.forEach(src => {
        const card = document.createElement('div');
        card.className = 'source-card';
        const score = (1 / (1 + (src.similarity_score || 0))).toFixed(2);
        card.innerHTML = `📄 Source: <a href="${src.url}" target="_blank">${escapeHtml(src.title || src.url)}</a> (Match: ${score})`;
        msgDiv.appendChild(card);
    });

    const box = document.getElementById("messages");
    if (box) box.scrollTop = box.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById("question");
    if (!input) return;

    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    appendMessage("user", text);

    const sendBtn = document.querySelector(".send");
    if (sendBtn) sendBtn.disabled = true;

    // Add typing bubble
    const box = document.getElementById("messages");
    const typing = document.createElement("div");
    typing.className = "msg ai";
    typing.id = "typingBubble";
    typing.innerHTML = `<div class="typing"><span></span><span></span><span></span></div>`;
    if (box) {
        box.appendChild(typing);
        box.scrollTop = box.scrollHeight;
    }

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text, kb_id: kbId, session_id: sessionId})
        });

        if (typing) typing.remove();

        if (!response.ok) {
            appendMessage("ai", "Sorry, an error occurred while connecting to the AI model.");
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let assistantContent = '';
        let sourcesData = null;
        let aiMsgDiv = appendMessage("ai", '');

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, {stream: true});
            const lines = chunk.split('\n').filter(line => line.trim() !== '');

            for (let line of lines) {
                try {
                    const data = JSON.parse(line);
                    if (data.type === 'sources') {
                        sourcesData = data.data;
                    } else if (data.type === 'chunk') {
                        assistantContent += data.data;
                        if (aiMsgDiv) {
                            aiMsgDiv.innerHTML = typeof marked !== 'undefined' ? marked.parse(assistantContent) : assistantContent;
                        }
                        if (box) box.scrollTop = box.scrollHeight;
                    } else if (data.type === 'error') {
                        assistantContent += data.data;
                        if (aiMsgDiv) aiMsgDiv.innerText = assistantContent;
                    }
                } catch (e) {
                    console.error("Stream parse error", e);
                }
            }
        }

        if (sourcesData && aiMsgDiv) {
            renderSources(sourcesData, aiMsgDiv);
        }

        if (aiMsgDiv) addCopyButtons(aiMsgDiv);

    } catch (e) {
        if (typing) typing.remove();
        appendMessage("ai", "Connection error. Please check backend server status.");
    } finally {
        if (sendBtn) sendBtn.disabled = false;
        input.focus();
    }
}

function addCopyButtons(container) {
    if (!container) return;
    const blocks = container.querySelectorAll('pre');
    blocks.forEach(block => {
        if (block.querySelector('.copy-btn')) return;

        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.innerText = 'Copy';

        btn.onclick = () => {
            const code = block.querySelector('code');
            const codeText = code ? code.innerText : block.innerText;
            navigator.clipboard.writeText(codeText);
            btn.innerText = 'Copied!';
            setTimeout(() => {
                btn.innerText = 'Copy';
            }, 2000);
        };

        block.appendChild(btn);
    });
}

function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[m]));
}
