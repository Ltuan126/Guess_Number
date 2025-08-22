// === game.js (đã cập nhật để sử dụng Socket.IO thay vì WebSocket) ===
const params = new URLSearchParams(window.location.search);
const room = (params.get("room") || "lobby").trim();

// Kết nối Socket.IO thay vì WebSocket
const socket = io("http://localhost:5000", {
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 500,
});

let username;
let currentRoom = room;

// Lưu trạng thái vào localStorage để khôi phục khi refresh
function saveGameState() {
  if (username && currentRoom) {
    localStorage.setItem('guessNumberGame', JSON.stringify({
      username: username,
      room: currentRoom,
      timestamp: Date.now()
    }));
  }
}

function loadGameState() {
  try {
    const saved = localStorage.getItem('guessNumberGame');
    if (saved) {
      const state = JSON.parse(saved);
      // Kiểm tra xem state có còn hợp lệ không (không quá 1 giờ)
      if (Date.now() - state.timestamp < 3600000) {
        username = state.username;
        currentRoom = state.room;
        
        // Cập nhật UI
        if (document.getElementById("username")) {
          document.getElementById("username").value = username;
        }
        if (document.getElementById("room")) {
          document.getElementById("room").value = currentRoom;
        }
        
        console.log("🔄 Khôi phục trạng thái game:", { username, currentRoom });
        return true;
      }
    }
  } catch (e) {
    console.log("❌ Lỗi khi khôi phục trạng thái:", e);
  }
  return false;
}

// Cache elements
const joinBtn = document.getElementById("joinBtn");
const createBtn = document.getElementById("createBtn");
const joinScreen = document.getElementById("join-screen");
const gameScreen = document.getElementById("game-screen");
const chatBox = document.getElementById("chatBox");
const leaderboardList = document.getElementById("leaderboardList");
const result = document.getElementById("result");
const joinStatus = document.getElementById("joinStatus");

// ---- Helper function to show status messages
function showStatus(message, type = "info", target = "both") {
  const statusMessage = message;
  
  if (target === "both" || target === "join") {
    if (joinStatus) {
      joinStatus.textContent = statusMessage;
      joinStatus.className = `status ${type}`;
    }
  }
  
  if (target === "both" || target === "game") {
    if (result) {
      result.textContent = statusMessage;
    }
  }
}

// ---- Core functions
function switchScreen() {
  username = document.getElementById("username").value.trim() || "Khách";
  currentRoom = document.getElementById("room").value.trim() || "lobby";

  // Ẩn màn hình join, hiện gameplay
  joinScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");

  // Kết nối Socket.IO và tham gia phòng
  if (socket.connected) {
    joinRoom();
  } else {
    socket.on("connect", joinRoom);
  }
}

function joinRoom() {
  // Chỉ sử dụng event mới join_room
  socket.emit("join_room", { 
    room_id: currentRoom, 
    player_name: username 
  });
}

// ---- Socket.IO event handlers
socket.on("connect", () => {
  console.log("✅ Kết nối Socket.IO thành công:", socket.id);
  showStatus("✅ Đã kết nối tới máy chủ", "success", "join");
  
  // Nếu có username và đang ở game screen, tự động tham gia lại phòng
  if (username && gameScreen && !gameScreen.classList.contains("hidden")) {
    console.log("🔄 Tự động tham gia lại phòng sau khi kết nối lại");
    joinRoom();
  }
});

socket.on("disconnect", (reason) => {
  console.log("❌ Mất kết nối:", reason);
  showStatus("❌ Mất kết nối tới máy chủ", "error", "both");
});

socket.on("reconnect", () => {
  console.log("✅ Kết nối lại thành công!");
  showStatus("✅ Đã kết nối lại thành công!", "success", "both");
  
  // Nếu có username và đang ở game screen, tự động tham gia lại phòng
  if (username && gameScreen && !gameScreen.classList.contains("hidden")) {
    console.log("🔄 Tự động tham gia lại phòng sau khi kết nối lại");
    joinRoom();
  }
});

socket.on("connect_error", (error) => {
  console.log("❌ Lỗi kết nối:", error);
  showStatus(`❌ Lỗi kết nối: ${error.message}`, "error", "join");
});

// ---- Modern Game events (ưu tiên sử dụng)
socket.on("room_joined", (data) => {
  console.log("🎉 Tham gia phòng thành công:", data);
  showStatus(`✅ Đã tham gia phòng ${data.room_name || currentRoom}`, "success", "game");
  
  // Lưu trạng thái game
  saveGameState();
  
  // Hiển thị thông tin phòng
  if (data.room_info) {
    // Hiển thị bảng điểm hiện tại
    if (data.room_info.scores) {
      updateLeaderboard(data.room_info.scores);
    }
    
    // Hiển thị thông tin vòng hiện tại
    if (data.room_info.current_round) {
      const round = data.room_info.current_round;
      showStatus(`🎮 Vòng ${data.room_info.round_number}: Đoán số từ ${round.range[0]} đến ${round.range[1]}`, "info", "game");
    }
    
    // Hiển thị danh sách người chơi
    if (data.room_info.players && data.room_info.players.length > 0) {
      console.log("👥 Người chơi trong phòng:", data.room_info.players);
    }
  }
});

socket.on("join_error", (data) => {
  console.log("❌ Lỗi tham gia phòng:", data.error);
  showStatus(`❌ Lỗi: ${data.error}`, "error", "both");
});

socket.on("player_joined", (data) => {
  console.log("👋 Người chơi tham gia:", data.player_name);
  showStatus(`👋 ${data.player_name} đã tham gia phòng`, "info", "game");
});

socket.on("player_left", (data) => {
  console.log("👋 Người chơi rời phòng:", data.player_name);
  showStatus(`👋 ${data.player_name} đã rời phòng`, "info", "game");
});

socket.on("new_round", (data) => {
  console.log("🎮 Vòng mới:", data);
  const roundNum = data.round_number || "?";
  const range = data.range || [1, 100];
  showStatus(`🎮 Vòng ${roundNum} bắt đầu! Đoán số từ ${range[0]} đến ${range[1]}`, "info", "game");
});

socket.on("guess_result", (data) => {
  console.log("💡 Kết quả đoán:", data);
  showStatus(data.message || "Kết quả đoán", "info", "game");
});

socket.on("guess_error", (data) => {
  console.log("❌ Lỗi đoán:", data.error);
  showStatus(`❌ Lỗi: ${data.error}`, "error", "game");
});

socket.on("chat_message", (data) => {
  console.log("💬 Chat:", data);
  if (chatBox) {
    const p = document.createElement("p");
    p.innerHTML = `<b>${data.player_name || "Ẩn danh"}:</b> ${data.message || ""}`;
    chatBox.appendChild(p);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
});

socket.on("chat_error", (data) => {
  console.log("❌ Lỗi chat:", data.error);
  showStatus(`❌ Lỗi chat: ${data.error}`, "error", "game");
});

socket.on("scoreboard_updated", (data) => {
  console.log("🏆 Bảng điểm cập nhật:", data);
  updateLeaderboard(data.scores || {});
});

socket.on("room_reset", (data) => {
  console.log("🔄 Phòng reset:", data);
  showStatus(`🔄 Phòng đã được reset: ${data.message}`, "info", "game");
  // Reset UI
  if (chatBox) chatBox.innerHTML = "";
  updateLeaderboard({});
});

// ---- Legacy events (để tương thích ngược)
socket.on("round", (data) => {
  console.log("📊 Vòng:", data);
  const roundId = data?.round ?? "?";
  const range = data?.range || [1, 100];
  showStatus(`📊 Vòng ${roundId} - Đoán số từ ${range[0]} đến ${range[1]}`, "info", "game");
});

socket.on("scoreboard", (data) => {
  console.log("🏆 Bảng điểm:", data);
  const scores = data?.scores || data || {};
  updateLeaderboard(scores);
});

socket.on("message", (data) => {
  console.log("📢 Tin nhắn:", data);
  const msg = data?.msg ?? "";
  showStatus(`📢 ${msg}`, "info", "game");
});

socket.on("result", (data) => {
  console.log("🎯 Kết quả:", data);
  const msg = data?.msg ?? "";
  showStatus(`🎯 ${msg}`, "info", "game");
});

socket.on("chat", (data) => {
  console.log("💬 Chat (legacy):", data);
  if (chatBox) {
    const p = document.createElement("p");
    p.innerHTML = `<b>${data.username || "Ẩn danh"}:</b> ${data.message || ""}`;
    chatBox.appendChild(p);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
});

socket.on("error", (data) => {
  console.log("❌ Lỗi:", data);
  const msg = data?.msg || data?.message || "Lỗi không xác định";
  showStatus(`❌ ${msg}`, "error", "both");
});

// ---- Helper functions
function updateLeaderboard(scores) {
  if (!leaderboardList) return;
  
  leaderboardList.innerHTML = "";
  
  if (Object.keys(scores).length === 0) {
    const li = document.createElement("li");
    li.textContent = "Chưa có điểm số";
    leaderboardList.appendChild(li);
    return;
  }
  
  Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .forEach(([name, score]) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${name}</span><span>${score} pts</span>`;
      leaderboardList.appendChild(li);
    });
}

// ---- Event listeners
joinBtn.addEventListener("click", switchScreen);
createBtn.addEventListener("click", switchScreen);

// Gửi chat
document.getElementById("sendChat").addEventListener("click", () => {
  const msgInput = document.getElementById("chatMsg");
  const msg = msgInput.value;
  if (msg.trim() !== "" && socket && socket.connected) {
    // Chỉ sử dụng event mới chat_message
    socket.emit("chat_message", { 
      room_id: currentRoom, 
      message: msg 
    });
    
    msgInput.value = "";
  }
});

// Gửi đoán số
document.getElementById("guessBtn").addEventListener("click", () => {
  const v = document.getElementById("guessInput").value;
  const guess = parseInt(v, 10);
  if (!Number.isNaN(guess) && socket && socket.connected) {
    // Chỉ sử dụng event mới make_guess
    socket.emit("make_guess", { 
      room_id: currentRoom, 
      guess: guess 
    });
    
    document.getElementById("guessInput").value = "";
  }
});

// Enter để gửi nhanh
document.getElementById("chatMsg").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    document.getElementById("sendChat").click();
  }
});

document.getElementById("guessInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    document.getElementById("guessBtn").click();
  }
});

// ---- Auto-join if room parameter exists
if (room && room !== "lobby") {
  console.log("📝 Phòng được chỉ định:", room);
  showStatus(`📝 Phòng được chỉ định: ${room}`, "info", "join");
} else {
  console.log("🏠 Phòng mặc định: lobby");
  showStatus("🏠 Phòng mặc định: lobby", "info", "join");
}

// Khôi phục trạng thái game khi trang load
document.addEventListener('DOMContentLoaded', () => {
  console.log("🔄 Đang khôi phục trạng thái game...");
  if (loadGameState()) {
    console.log("✅ Khôi phục trạng thái thành công:", { username, currentRoom });
    showStatus(`🔄 Đã khôi phục: ${username} trong phòng ${currentRoom}`, "info", "join");
  }
});
