(function () {
  "use strict";

  var STORAGE_KEY = "medrag_conversations_v1";

  var chatOuter = document.getElementById("chat");
  var composer = document.getElementById("composer");
  var input = document.getElementById("question-input");
  var sendBtn = document.getElementById("send-btn");
  var statusDot = document.getElementById("status-dot");
  var conversationList = document.getElementById("conversation-list");
  var newChatBtn = document.getElementById("new-chat-btn");
  var shell = document.getElementById("shell");
  var sidebarToggle = document.getElementById("sidebar-toggle");
  var sidebarBackdrop = document.getElementById("sidebar-backdrop");

  // Wrap the chat contents in a width-capped inner column; chatOuter stays
  // the scrolling element, chatInner is what we actually append messages to.
  var chatInner = document.createElement("div");
  chatInner.id = "chat-inner";
  chatInner.className = "chat-inner";
  while (chatOuter.firstChild) {
    chatInner.appendChild(chatOuter.firstChild);
  }
  chatOuter.appendChild(chatInner);

  var VERDICT_CLASS = {
    supported: "ok",
    partially_supported: "warn",
    off_topic: "bad",
    unsupported: "bad",
  };

  function verdictClass(verdict) {
    return VERDICT_CLASS[verdict] || "neutral";
  }

  function scrollToBottom() {
    chatOuter.scrollTop = chatOuter.scrollHeight;
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function uid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "id-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
  }

  function deriveTitle(question) {
    var t = question.trim();
    if (t.length > 42) t = t.slice(0, 42).trim() + "\u2026";
    return t || "New chat";
  }

  // ---------- persistence ----------

  function blankConversation() {
    var now = new Date().toISOString();
    return { id: uid(), title: "New chat", messages: [], createdAt: now, updatedAt: now };
  }

  function loadState() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.conversations) || !parsed.conversations.length) return null;
      return parsed;
    } catch (e) {
      return null;
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      /* storage unavailable (private mode, quota) -- history just won't persist */
    }
  }

  function findConversation(id) {
    for (var i = 0; i < state.conversations.length; i++) {
      if (state.conversations[i].id === id) return state.conversations[i];
    }
    return null;
  }

  function activeConversation() {
    return findConversation(state.activeId) || state.conversations[0];
  }

  var state = loadState();
  if (!state) {
    var fresh = blankConversation();
    state = { conversations: [fresh], activeId: fresh.id };
    saveState();
  }
  if (!state.activeId || !findConversation(state.activeId)) {
    state.activeId = state.conversations[0].id;
  }

  // ---------- sidebar rendering ----------

  function sortedConversations() {
    return state.conversations.slice().sort(function (a, b) {
      return new Date(b.updatedAt) - new Date(a.updatedAt);
    });
  }

  function renderSidebar() {
    conversationList.innerHTML = "";
    sortedConversations().forEach(function (conv) {
      var li = el("li", "conversation-item" + (conv.id === state.activeId ? " active" : ""));

      var titleBtn = el("button", "conv-title", conv.title);
      titleBtn.type = "button";
      titleBtn.addEventListener("click", function () {
        setActiveConversation(conv.id);
      });
      li.appendChild(titleBtn);

      var actions = el("div", "conv-actions");

      var renameBtn = el("button", "icon-btn", "\u270e");
      renameBtn.type = "button";
      renameBtn.title = "Rename";
      renameBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        startRename(conv, titleBtn);
      });
      actions.appendChild(renameBtn);

      var deleteBtn = el("button", "icon-btn danger", "\u2715");
      deleteBtn.type = "button";
      deleteBtn.title = "Delete";
      var confirmTimer = null;
      deleteBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        if (deleteBtn.classList.contains("confirm")) {
          clearTimeout(confirmTimer);
          deleteConversation(conv.id);
        } else {
          deleteBtn.classList.add("confirm");
          deleteBtn.title = "Click again to confirm";
          confirmTimer = setTimeout(function () {
            deleteBtn.classList.remove("confirm");
            deleteBtn.title = "Delete";
          }, 2500);
        }
      });
      actions.appendChild(deleteBtn);

      li.appendChild(actions);
      conversationList.appendChild(li);
    });
  }

  function startRename(conv, titleBtn) {
    var inputEl = document.createElement("input");
    inputEl.type = "text";
    inputEl.className = "conv-title editing";
    inputEl.value = conv.title;
    titleBtn.replaceWith(inputEl);
    inputEl.focus();
    inputEl.select();

    function commit() {
      var val = inputEl.value.trim();
      conv.title = val || conv.title;
      saveState();
      renderSidebar();
    }

    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        commit();
      } else if (e.key === "Escape") {
        renderSidebar();
      }
    });
    inputEl.addEventListener("blur", commit);
  }

  function setActiveConversation(id) {
    state.activeId = id;
    saveState();
    renderSidebar();
    renderChatFromActive();
    closeSidebarOnMobile();
  }

  function deleteConversation(id) {
    var idx = -1;
    for (var i = 0; i < state.conversations.length; i++) {
      if (state.conversations[i].id === id) { idx = i; break; }
    }
    if (idx === -1) return;
    state.conversations.splice(idx, 1);
    if (state.conversations.length === 0) {
      state.conversations.push(blankConversation());
    }
    if (state.activeId === id) {
      state.activeId = sortedConversations()[0].id;
    }
    saveState();
    renderSidebar();
    renderChatFromActive();
  }

  newChatBtn.addEventListener("click", function () {
    var conv = blankConversation();
    state.conversations.unshift(conv);
    state.activeId = conv.id;
    saveState();
    renderSidebar();
    renderChatFromActive();
    closeSidebarOnMobile();
    input.focus();
  });

  // ---------- sidebar toggle (mobile) ----------

  function closeSidebarOnMobile() {
    shell.classList.remove("sidebar-open");
  }

  sidebarToggle.addEventListener("click", function () {
    shell.classList.toggle("sidebar-open");
  });
  sidebarBackdrop.addEventListener("click", closeSidebarOnMobile);

  // ---------- chat rendering ----------

  function clearChat() {
    chatInner.innerHTML = "";
  }

  function showEmptyState() {
    var wrap = el("div", "empty-state");
    wrap.appendChild(el("p", null, "Ask a question about the corpus:"));
    var list = el("ul");
    ["Hypertension", "Diabetes", "Asthma", "Bacterial infections", "Depression"].forEach(function (topic) {
      list.appendChild(el("li", null, topic));
    });
    wrap.appendChild(list);
    chatInner.appendChild(wrap);
  }

  function buildUserBubble(question) {
    var wrap = el("div", "msg user");
    wrap.appendChild(el("div", "bubble-user", question));
    return wrap;
  }

  function buildAnswerCard(message) {
    var wrap = el("div", "msg");
    var card = el("div", "card");

    var head = el("div", "card-head");
    head.appendChild(el("b", null, "Answer"));
    var verdict = (message.verification && message.verification.verdict) || "unverified";
    head.appendChild(el("span", "badge " + verdictClass(verdict), verdict));
    card.appendChild(head);

    card.appendChild(el("p", "answer", message.answer || ""));

    var claims = (message.verification && message.verification.unsupported_claims) || [];
    if (claims.length) {
      var claimsList = el("ul", "claims");
      claims.forEach(function (c) {
        claimsList.appendChild(el("li", null, c));
      });
      card.appendChild(claimsList);
    }

    var sources = message.sources || [];
    if (sources.length) {
      var sourcesRow = el("div", "sources");
      sources.forEach(function (s, i) {
        var chip = document.createElement("a");
        chip.className = "chip";
        chip.href = s.url || "#";
        chip.target = "_blank";
        chip.rel = "noopener";
        chip.appendChild(el("em", null, String(i + 1)));
        chip.appendChild(el("span", null, s.title || s.url || "source"));
        sourcesRow.appendChild(chip);
      });
      card.appendChild(sourcesRow);
    }

    var latency = typeof message.latency_ms === "number" ? message.latency_ms + "ms" : "?";
    card.appendChild(
      el(
        "div",
        "meta",
        latency + " \u00b7 " + sources.length + " sources \u00b7 verified against retrieved context"
      )
    );

    wrap.appendChild(card);
    return wrap;
  }

  function buildErrorCard(message) {
    var wrap = el("div", "msg");
    wrap.appendChild(el("div", "card error", message.message || "Something went wrong."));
    return wrap;
  }

  function renderChatFromActive() {
    clearChat();
    var conv = activeConversation();
    if (!conv.messages.length) {
      showEmptyState();
      return;
    }
    conv.messages.forEach(function (m) {
      if (m.role === "user") {
        chatInner.appendChild(buildUserBubble(m.content));
      } else if (m.role === "assistant") {
        chatInner.appendChild(buildAnswerCard(m));
      } else if (m.role === "error") {
        chatInner.appendChild(buildErrorCard(m));
      }
    });
    scrollToBottom();
  }

  // ---------- asking questions ----------

  function setBusy(busy) {
    input.disabled = busy;
    sendBtn.disabled = busy;
  }

  composer.addEventListener("submit", function (e) {
    e.preventDefault();
    var question = input.value.trim();
    if (!question) return;

    var conv = activeConversation();
    var isFirstMessage = conv.messages.length === 0;

    conv.messages.push({ role: "user", content: question });
    conv.updatedAt = new Date().toISOString();
    if (isFirstMessage) {
      conv.title = deriveTitle(question);
    }
    saveState();
    renderSidebar();

    if (chatInner.querySelector(".empty-state")) clearChat();
    chatInner.appendChild(buildUserBubble(question));

    var pendingWrap = el("div", "msg");
    pendingWrap.appendChild(el("div", "card pending", "Thinking\u2026"));
    chatInner.appendChild(pendingWrap);
    scrollToBottom();

    input.value = "";
    setBusy(true);

    fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question }),
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("Server returned " + res.status);
        }
        return res.json();
      })
      .then(function (data) {
        var message = {
          role: "assistant",
          answer: data.answer,
          sources: data.sources,
          verification: data.verification,
          latency_ms: data.latency_ms,
        };
        conv.messages.push(message);
        conv.updatedAt = new Date().toISOString();
        saveState();
        renderSidebar();
        pendingWrap.replaceWith(buildAnswerCard(message));
        scrollToBottom();
      })
      .catch(function (err) {
        var message = {
          role: "error",
          message: "Couldn't reach MedRAG Copilot (" + err.message + "). Is the server running?",
        };
        conv.messages.push(message);
        conv.updatedAt = new Date().toISOString();
        saveState();
        pendingWrap.replaceWith(buildErrorCard(message));
        scrollToBottom();
      })
      .finally(function () {
        setBusy(false);
        input.focus();
      });
  });

  // ---------- health check ----------

  function checkHealth() {
    fetch("/health")
      .then(function (res) {
        if (!res.ok) throw new Error("not ok");
        statusDot.classList.remove("offline");
      })
      .catch(function () {
        statusDot.classList.add("offline");
      });
  }

  // ---------- init ----------

  renderSidebar();
  renderChatFromActive();
  checkHealth();
  input.focus();
})();