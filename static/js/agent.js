let sessionKey = localStorage.getItem("agent_session_key") || null;

window.addEventListener("DOMContentLoaded", loadHistory);

async function loadHistory() {
    if (!sessionKey) return;
    try {
        const response = await fetch(`/agent/history/${sessionKey}`);
        const data = await response.json();
        if (data.messages && data.messages.length > 0) {
            const chatWindow = document.getElementById("chat-window");
            chatWindow.innerHTML = "";
            data.messages.forEach(msg => {
                if (msg.role === "user") {
                    chatWindow.innerHTML += `<div class="msg-block"><div class="chat-bubble-user">${msg.content}</div></div>`;
                } else {
                    const structuredHtml = renderStructuredResult(msg.tool_used, msg.result);
                    const tag = msg.tool_used ? `<div class="tool-tag"><i class="bi bi-tools"></i> ${msg.tool_used}</div>` : "";
                    chatWindow.innerHTML += `<div class="msg-block"><div class="chat-bubble-bot">${msg.content}${structuredHtml}${tag}</div></div>`;
                }
            });
            chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
        }
    } catch (err) { console.error(err); }
}
document.querySelectorAll(".quick-action").forEach(btn => {
    btn.addEventListener("click", function () {
        document.getElementById("user-input").value = this.dataset.text;
        document.getElementById("chat-form").dispatchEvent(new Event("submit"));
    });
});

document.getElementById("chat-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    const chatWindow = document.getElementById("chat-window");
    if (chatWindow.querySelector(".text-muted.text-center")) chatWindow.innerHTML = "";

    chatWindow.innerHTML += `<div class="msg-block"><div class="chat-bubble-user">${message}</div></div>`;
    input.value = "";
    chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });

    const loadingId = "loading-" + Date.now();
    chatWindow.innerHTML += `<div class="msg-block" id="${loadingId}"><div class="chat-bubble-bot"><div class="agent-status" id="status-${loadingId}"></div></div></div>`;
    chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });

    const statusEl = document.getElementById(`status-${loadingId}`);
    const stopStatusSequence = runStatusSequence(statusEl);

    try {
        const response = await fetch("/agent/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, session_key: sessionKey })
        });

        if (!response.ok) {
            stopStatusSequence();
            document.getElementById(loadingId).outerHTML =
                `<div class="msg-block"><div class="chat-bubble-bot error-bubble"><i class="bi bi-exclamation-triangle"></i> Something went wrong on the server (error ${response.status}). Please try again.</div></div>`;
            return;
        }

        const data = await response.json();

        if (data.session_key) {
            sessionKey = data.session_key;
            localStorage.setItem("agent_session_key", sessionKey);
        }

        stopStatusSequence();

        // Brief final status before showing the answer
        statusEl.innerHTML = statusHTML("bi-check-circle", "Producing final response", "status-done");
        await new Promise(r => setTimeout(r, 350));

        let tag = "";
        if (data.needs_approval) {
            tag = `<div class="approval-tag"><i class="bi bi-hourglass-split"></i> Awaiting your approval — check the Approvals tab</div>`;
        } else if (data.tool_used) {
            tag = `<div class="tool-tag"><i class="bi bi-tools"></i> ${data.tool_used}</div>`;
        }

        const structuredHtml = renderStructuredResult(data.tool_used, data.result);
        const isError = data.reply && (data.reply.toLowerCase().includes("something went wrong") || data.reply.toLowerCase().includes("couldn't complete") || data.reply.toLowerCase().includes("not found"));

        const msgBlock = document.createElement("div");
        msgBlock.className = "msg-block";
        msgBlock.innerHTML = `<div class="chat-bubble-bot ${isError ? 'error-bubble' : ''}"></div>`;
        document.getElementById(loadingId).replaceWith(msgBlock);

        const bubbleEl = msgBlock.querySelector(".chat-bubble-bot");
        const finalHtml = (isError ? `<i class="bi bi-exclamation-triangle"></i> ` : '') + data.reply + structuredHtml + tag;
        typeWriterEffect(bubbleEl, data.reply, finalHtml, 10);

        if (window.refreshApprovalBadge) window.refreshApprovalBadge();

    } catch (err) {
        stopStatusSequence();
        document.getElementById(loadingId).outerHTML =
            `<div class="msg-block"><div class="chat-bubble-bot error-bubble"><i class="bi bi-exclamation-triangle"></i> Network error — please check your connection and try again.</div></div>`;
    }
});

function statusHTML(icon, label, extraClass = "") {
    return `<span class="agent-status-item ${extraClass}"><i class="bi ${icon}"></i> ${label}</span>`;
}

function runStatusSequence(statusEl) {
    const steps = [
        { icon: "bi-cpu", label: "Thinking", delay: 0 },
        { icon: "bi-signpost-2", label: "Analyzing intent", delay: 900 },
        { icon: "bi-tools", label: "Selecting tool", delay: 1900 },
        { icon: "bi-gear-wide-connected", label: "Executing", delay: 2900 },
    ];

    const timeouts = steps.map(step =>
        setTimeout(() => {
            statusEl.innerHTML = statusHTML(step.icon, step.label);
        }, step.delay)
    );

    // Initial state immediately
    statusEl.innerHTML = statusHTML(steps[0].icon, steps[0].label);

    return function stop() {
        timeouts.forEach(t => clearTimeout(t));
    };
}
function priorityBadge(priority) {
    if (!priority) return "";
    return `<span class="priority-badge priority-${priority}">${priority}</span>`;
}

function renderStructuredResult(toolName, result) {
    if (!result) return "";

    // Task list style tools
    if (["list_tasks", "create_tasks_from_text", "generate_daily_plan", "generate_weekly_plan"].includes(toolName)) {
    const tasks = result.tasks || [];
    let html = "";

    if (tasks.length > 0) {
        const rows = tasks.map(t => `
            <div class="result-list-item">
                <span>${t.suggested_time ? `<span class="time-slot">${t.suggested_time}</span> ` : ''}${t.title}</span>
                <span>${priorityBadge(t.priority)} ${t.due_date ? `<span class="text-muted" style="font-size:11px;">${t.due_date.split(' ')[0]}</span>` : ''}</span>
            </div>
        `).join("");
        html += `<div class="result-card"><div class="result-card-header">${tasks.length} task(s)</div>${rows}</div>`;
    }

    if (result.focus_areas && result.focus_areas.length > 0) {
        html += `<div class="recommendation-box"><i class="bi bi-bullseye"></i> ${result.focus_areas.join(" · ")}</div>`;
    }

    if (result.deferred && result.deferred.length > 0) {
        const deferredRows = result.deferred.map(t => `
            <div class="result-list-item"><span>${t.title}</span>${priorityBadge(t.priority)}</div>
        `).join("");
        html += `<div class="result-card" style="margin-top:10px;"><div class="result-card-header">Deferred (${result.deferred.length})</div>${deferredRows}</div>`;
    }

    if (result.risk_warnings && result.risk_warnings.length > 0) {
        const warningsHtml = result.risk_warnings.map(w => `<div class="risk-warning"><i class="bi bi-exclamation-triangle"></i> ${w}</div>`).join("");
        html += warningsHtml;
    }

    return html;
    }

    // Productivity report
    if (toolName === "generate_productivity_report") {
        return `<div class="result-card">
            <div class="stat-grid">
                <div class="stat-box"><div class="stat-num">${result.completed_count}</div><div class="stat-label">Completed</div></div>
                <div class="stat-box"><div class="stat-num">${result.pending_count}</div><div class="stat-label">Pending</div></div>
                <div class="stat-box"><div class="stat-num">${result.overdue_count}</div><div class="stat-label">Overdue</div></div>
                <div class="stat-box"><div class="stat-num">${result.high_priority_pending_count}</div><div class="stat-label">High Priority</div></div>
            </div>
        </div>`;
    }

    // Notes search
    if (toolName === "search_notes") {
        const notes = result.notes || [];
        if (notes.length === 0) return "";
        const rows = notes.map(n => `
            <div class="result-list-item" style="flex-direction:column; align-items:flex-start;">
                <strong style="font-size:12.5px;">${n.title}</strong>
                <span class="text-muted" style="font-size:12px;">${n.content}</span>
            </div>
        `).join("");
        return `<div class="result-card"><div class="result-card-header">${notes.length} note(s) found</div>${rows}</div>`;
    }

    // Email draft
    if (toolName === "draft_email" && result.draft) {
        const escaped = result.draft.replace(/`/g, "\\`");
        return `<div class="email-draft-box">${result.draft}<button class="copy-btn" onclick="navigator.clipboard.writeText(\`${escaped}\`); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy',1500)">Copy</button></div>`;
    }

    return "";
}

function typeWriterEffect(element, plainText, finalHtml, speed = 10) {
    const words = plainText.split(/(\s+)/);
    let i = 0;
    element.textContent = "";

    function typeNext() {
        if (i < words.length) {
            element.textContent += words[i];
            i++;
            const chatWindow = document.getElementById("chat-window");
            chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
            setTimeout(typeNext, speed);
        } else {
            element.innerHTML = finalHtml;
        }
    }
    typeNext();
}