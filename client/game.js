// === game.js (đã chỉnh từ file gốc) ===
const params = new URLSearchParams(window.location.search);
const room = (params.get("room") || "lobby").trim();

const socket = io("http://localhost:5000", {
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 500,
});

let playerName = localStorage.getItem("playerName") || "";
let joined = false;

// Cache element helpers
const $ = (id) => document.getElementById(id);
const elLog = $("log");
const elChat = $("chatBox");
const elScore = $("scoreboard");
const elTimer = $("timer");
const elRound = $("round");
const elName = $("name");
const elGuess = $("guess");
const elChatInput = $("chatInput");
const elJoinBtn = $("joinBtn") || $("join") || null;
const elSendBtn = $("sendBtn") || $("send") || null;

// ---- Small utils
function safeAppend(el, html) {
  if (!el) return;
  const div = document.createElement("div");
  div.innerHTML = html;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}
function log(msg) {
  safeAppend(elLog, msg);
}
function appendChat(msg) {
  safeAppend(elChat, msg);
}
function isIntLike(v) {
  return /^-?\d+$/.test(String(v).trim());
}

// ---- UI state
function setJoinedState(state) {
  joined = state;
  if (elGuess) elGuess.disabled = !state;
  if (elSendBtn) elSendBtn.disabled = !state;
}
setJoinedState(false);

// Prefill name if available
if (elName && playerName) elName.value = playerName;

// ---- Core actions
function joinGame() {
  const nameInput = (elName?.value || "").trim();
  playerName = nameInput || playerName || "Player";
  localStorage.setItem("playerName", playerName);
  socket.emit("join", { room, name: playerName });
}

function sendGuess() {
  if (!joined) return alert("Nhập tên và bấm Vào game trước!");
  const val = elGuess?.value ?? "";
  if (!isIntLike(val)) return alert("Hãy nhập một số nguyên hợp lệ!");
  socket.emit("guess", { room, name: playerName, number: parseInt(val, 10) });
  elGuess.value = "";
  elGuess.focus();
}

function sendChat() {
  if (!joined) return alert("Nhập tên và bấm Vào game trước!");
  const t = (elChatInput?.value || "").trim();
  if (!t) return;
  socket.emit("chat", { room, name: playerName, text: t });
  elChatInput.value = "";
  elChatInput.focus();
}

// ---- Event wiring (buttons + Enter)
elJoinBtn && elJoinBtn.addEventListener("click", joinGame);
elSendBtn && elSendBtn.addEventListener("click", sendGuess);
elGuess &&
  elGuess.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendGuess();
  });
elChatInput &&
  elChatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChat();
  });

// ---- Countdown
function startCountdown(endsAtMs) {
  if (!elTimer) return;
  clearInterval(window.__t);
  if (!endsAtMs || isNaN(endsAtMs)) {
    elTimer.textContent = "--";
    return;
  }
  window.__t = setInterval(() => {
    const left = Math.max(0, Math.floor((endsAtMs - Date.now()) / 1000));
    elTimer.textContent = left + "s";
    if (left <= 0) clearInterval(window.__t);
  }, 250);
}

// ---- Socket handlers
socket.on("connect", () => {
  log(`<i>Kết nối server: ${socket.id}</i>`);
  // Tự re-join sau khi reconnect
  if (playerName) {
    socket.emit("join", { room, name: playerName });
  }
});

socket.on("disconnect", (reason) => {
  log(`<i>Mất kết nối: ${reason}</i>`);
  setJoinedState(false);
});

socket.on("reconnect_attempt", (n) => {
  log(`<i>Đang thử kết nối lại… (lần ${n})</i>`);
});

socket.on("message", (d) => {
  const r = d?.room || room;
  const msg = d?.msg ?? "";
  log(`[${r}] ${msg}`);
});

socket.on("result", (d) => {
  const msg = d?.msg ?? "";
  log(`Kết quả: ${msg}`);
});

socket.on("error", (d) => {
  const msg = d?.msg ?? "";
  log(`Lỗi: ${msg}`);
});

socket.on("round", (d) => {
  const r = d?.room || room;
  const roundId = d?.round ?? "?";
  const range = d?.range || [1, 100];

  // Cập nhật tiêu đề vòng
  if (elRound)
    elRound.textContent = `Phòng ${r} – Vòng ${roundId} – [${range[0]}, ${range[1]}]`;
  startCountdown(d?.endsAt);
  log(`=== Vòng ${roundId} bắt đầu ===`);
  setJoinedState(true);

  // Hiển thị hint CHỈ ở hintBox
  const hintBox = document.getElementById("hintBox");
  if (hintBox) {
    if (d.hint) {
      hintBox.style.display = "block";
      hintBox.textContent = "💡 Gợi ý: " + d.hint;
    } else {
      hintBox.style.display = "none";
      hintBox.textContent = "";
    }
  }
});


socket.on("scoreboard", (d) => {
  const scores = d?.scores || d || {};
  if (!elScore) return;
  elScore.innerHTML = "";
  Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .forEach(([n, s]) => {
      const li = document.createElement("li");
      li.textContent = `${n}: ${s}`;
      elScore.appendChild(li);
    });
});

socket.on("chat", (d) => {
  const name = (d?.name || "Ẩn danh").toString().slice(0, 32);
  const text = (d?.text || "").toString().slice(0, 200);
  appendChat(`<b>${name}</b>: ${text}`);
});
