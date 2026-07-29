const API_BASE_URL = "/api";
const MAX_HISTORY_MESSAGES = 20;

const statusElement = document.querySelector("#api-status");
const statusTextElement = statusElement.querySelector(".status-text");
const keyBadge = document.querySelector("#key-badge");
const apiKeyWarning = document.querySelector("#api-key-warning");
const messageList = document.querySelector("#message-list");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const resetButton = document.querySelector("#reset-button");
const typingIndicator = document.querySelector("#typing-indicator");
const errorElement = document.querySelector("#error-message");
const characterCount = document.querySelector("#character-count");
const suggestions = document.querySelectorAll(".suggestion");

let messages = [];
let isSending = false;
let isOpenAIConfigured = false;

function setApiStatus(status, message) {
  statusElement.classList.remove(
    "status-checking",
    "status-online",
    "status-offline",
  );
  statusElement.classList.add(`status-${status}`);
  statusTextElement.textContent = message;
}

function setKeyStatus(configured) {
  isOpenAIConfigured = configured;
  keyBadge.classList.remove("key-checking", "key-ready", "key-missing");
  keyBadge.classList.add(configured ? "key-ready" : "key-missing");
  keyBadge.textContent = configured ? "API 키 설정됨" : "API 키 없음";
  apiKeyWarning.hidden = configured;
  updateSendButton();
}

function formatApiError(payload, status) {
  if (Array.isArray(payload?.detail)) {
    return payload.detail
      .map((item) => item.msg ?? JSON.stringify(item))
      .join(", ");
  }

  return payload?.detail ?? payload?.message ?? `HTTP ${status} 오류`;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.headers ?? {}),
    },
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(formatApiError(payload, response.status));
  }

  return payload;
}

function currentTime() {
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

function appendMessage(role, content) {
  const article = document.createElement("article");
  article.className = `message message-${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "assistant" ? "AI" : "나";

  const body = document.createElement("div");
  body.className = "message-body";

  const meta = document.createElement("div");
  meta.className = "message-meta";

  const author = document.createElement("strong");
  author.textContent = role === "assistant" ? "AI 어시스턴트" : "사용자";

  const time = document.createElement("span");
  time.textContent = currentTime();

  const text = document.createElement("p");
  text.textContent = content;

  meta.append(author, time);
  body.append(meta, text);
  article.append(avatar, body);
  messageList.append(article);
  messageList.scrollTop = messageList.scrollHeight;
}

function trimConversation() {
  while (messages.length > MAX_HISTORY_MESSAGES) {
    messages.splice(0, 2);
  }
}

function setSending(sending) {
  isSending = sending;
  typingIndicator.hidden = !sending;
  input.disabled = sending;
  updateSendButton();

  if (sending) {
    messageList.scrollTop = messageList.scrollHeight;
  }
}

function updateSendButton() {
  sendButton.disabled =
    isSending || !isOpenAIConfigured || input.value.trim().length === 0;
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
}

function updateCharacterCount() {
  characterCount.textContent = `${input.value.length} / 4000`;
  updateSendButton();
  resizeInput();
}

function showError(error) {
  errorElement.textContent = `메시지 전송 실패: ${error.message}`;
  errorElement.hidden = false;
}

async function checkBackend() {
  try {
    await fetchJson("/health");
    setApiStatus("online", "FastAPI 정상");
  } catch (error) {
    console.error(error);
    setApiStatus("offline", "FastAPI 연결 실패");
  }
}

async function loadServiceInfo() {
  try {
    const info = await fetchJson("/info");

    for (const [field, value] of Object.entries(info)) {
      const target = document.querySelector(`[data-field="${field}"]`);
      if (target) {
        target.textContent = String(value);
        target.title = String(value);
      }
    }

    setKeyStatus(Boolean(info.openai_configured));
  } catch (error) {
    console.error(error);
    keyBadge.textContent = "확인 실패";
    keyBadge.classList.add("key-missing");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const content = input.value.trim();
  if (!content || isSending || !isOpenAIConfigured) {
    return;
  }

  errorElement.hidden = true;
  messages.push({ role: "user", content });
  trimConversation();
  appendMessage("user", content);

  input.value = "";
  updateCharacterCount();
  setSending(true);

  try {
    const result = await fetchJson("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ messages }),
    });

    messages.push({ role: "assistant", content: result.reply });
    trimConversation();
    appendMessage("assistant", result.reply);
    setApiStatus("online", `${result.model} 응답 완료`);
  } catch (error) {
    console.error(error);
    messages.pop();
    showError(error);
    setApiStatus("offline", "AI 요청 실패");
  } finally {
    setSending(false);
    input.focus();
  }
});

input.addEventListener("input", updateCharacterCount);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

resetButton.addEventListener("click", () => {
  messages = [];
  messageList.innerHTML = "";
  appendMessage(
    "assistant",
    "대화를 초기화했습니다. 새로운 주제로 질문해 보세요.",
  );
  errorElement.hidden = true;
  input.focus();
});

for (const suggestion of suggestions) {
  suggestion.addEventListener("click", () => {
    input.value = suggestion.textContent.trim();
    updateCharacterCount();
    input.focus();
  });
}

updateCharacterCount();
checkBackend();
loadServiceInfo();
