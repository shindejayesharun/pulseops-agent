let conversationId = 'conv_' + Math.random().toString(36).substring(2, 14);

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const engineSelect = document.getElementById('engine-select');
const modeBadge = document.getElementById('mode-badge');
const modeText = document.getElementById('mode-text');
const newChatBtn = document.getElementById('new-chat-btn');

const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');
const tracesList = document.getElementById('traces-list');
const ticketsList = document.getElementById('tickets-list');
const prsList = document.getElementById('prs-list');
const traceCount = document.getElementById('trace-count');
const ticketCount = document.getElementById('ticket-count');
const prCount = document.getElementById('pr-count');

// Tab Switching
tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabPanes.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
  });
});

// Engine Select Change
engineSelect.addEventListener('change', (e) => {
  const mode = e.target.value;
  if (mode === 'live') {
    modeBadge.className = 'badge badge-live';
    modeText.textContent = 'Live OpenAI Mode';
  } else {
    modeBadge.className = 'badge badge-mock';
    modeText.textContent = 'Offline Mock Mode';
  }
});

// New Chat Button
newChatBtn.addEventListener('click', () => {
  conversationId = 'conv_' + Math.random().toString(36).substring(2, 14);
  chatMessages.innerHTML = `
    <div class="message assistant-msg">
      <div class="msg-sender">⚡ PulseOps System</div>
      <div class="msg-content">Started a fresh operational session. How can I assist?</div>
    </div>
  `;
  tracesList.innerHTML = '<div class="empty-state">No tool invocations in this session yet.</div>';
  traceCount.textContent = '0';
});

// Suggestion Chips
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    chatInput.value = chip.dataset.prompt;
    chatForm.dispatchEvent(new Event('submit'));
  });
});

// Submit Form
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage('user', text);
  chatInput.value = '';

  const loadingMsg = appendMessage('assistant', '<em>Reasoning across internal knowledge and tools...</em>');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: text,
        mode: engineSelect.value
      })
    });

    if (!res.ok) {
      throw new Error(`API error HTTP ${res.status}`);
    }

    const data = await res.json();
    loadingMsg.querySelector('.msg-content').innerHTML = formatMarkdown(data.response);

    // Refresh Traces & Artifacts
    fetchTraces();
    fetchArtifacts();

  } catch (err) {
    loadingMsg.querySelector('.msg-content').innerHTML = `<span style="color: var(--accent-red)">Error: ${err.message}</span>`;
  }
});

function appendMessage(role, text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}-msg`;
  msgDiv.innerHTML = `
    <div class="msg-sender">${role === 'user' ? '👤 Operator' : '⚡ PulseOps Agent'}</div>
    <div class="msg-content">${formatMarkdown(text)}</div>
  `;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return msgDiv;
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code style="background:#21262d;padding:2px 4px;border-radius:3px;">$1</code>');
}

async function fetchTraces() {
  try {
    const res = await fetch(`/api/traces/${conversationId}`);
    if (!res.ok) return;
    const data = await res.json();
    traceCount.textContent = data.count;

    if (data.traces.length === 0) {
      tracesList.innerHTML = '<div class="empty-state">No tool invocations in this session yet.</div>';
      return;
    }

    tracesList.innerHTML = data.traces.map(t => `
      <div class="trace-card">
        <div class="card-header">
          <span class="tool-badge">🔧 ${t.tool_name}</span>
          <span class="latency-pill">${t.latency_ms} ms</span>
        </div>
        <div style="font-size:11px;color:#8b949e;">Inputs:</div>
        <pre class="code-snippet">${JSON.stringify(t.args_json, null, 2)}</pre>
        <div style="font-size:11px;color:#8b949e;margin-top:6px;">Result:</div>
        <pre class="code-snippet">${JSON.stringify(t.result_json, null, 2)}</pre>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

async function fetchArtifacts() {
  try {
    const [tRes, pRes] = await Promise.all([
      fetch('/api/tickets'),
      fetch('/api/prs/summaries')
    ]);

    if (tRes.ok) {
      const tData = await tRes.json();
      ticketCount.textContent = tData.count;
      if (tData.tickets.length > 0) {
        ticketsList.innerHTML = tData.tickets.map(tk => `
          <div class="artifact-card">
            <div class="card-header">
              <strong style="color:var(--accent-amber);">${tk.id}</strong>
              <span class="badge" style="background:#30363d;color:#58a6ff;">${tk.priority}</span>
            </div>
            <div style="font-weight:600;margin-bottom:4px;">${tk.title}</div>
            <div style="font-size:12px;color:#8b949e;">Team: <strong>${tk.team}</strong> · Status: <em>${tk.status}</em></div>
            <p style="font-size:12px;margin-top:6px;color:#c9d1d9;">${tk.description}</p>
          </div>
        `).join('');
      }
    }

    if (pRes.ok) {
      const pData = await pRes.json();
      prCount.textContent = pData.count;
      if (pData.summaries.length > 0) {
        prsList.innerHTML = pData.summaries.map(pr => `
          <div class="artifact-card">
            <div class="card-header">
              <strong style="color:var(--accent-purple);">${pr.id} (PR #${pr.pr_number})</strong>
              <span class="badge" style="background:#30363d;color:#3fb950;">Risk: ${pr.risk_level}</span>
            </div>
            <p style="font-size:12px;color:#c9d1d9;margin-bottom:6px;">${pr.summary}</p>
            <div style="font-size:11px;color:#8b949e;"><strong>Risk Notes:</strong> ${pr.risk_notes}</div>
          </div>
        `).join('');
      }
    }
  } catch (err) {
    console.error(err);
  }
}

// Initial fetch
fetchArtifacts();
