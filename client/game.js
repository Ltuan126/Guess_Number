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

// Tạo mã phòng ngẫu nhiên
function generateRoomId() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// Cache elements - sẽ được khởi tạo khi DOM load
let joinBtn, createBtn, joinScreen, gameScreen, chatBox, leaderboardList, result, joinStatus;
let showRoomsBtn, roomsList, leaveRoomBtn, roundNumber, rangeStart, rangeEnd, copyRoomBtn;

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

// Hiển thị danh sách phòng có sẵn
function showAvailableRooms() {
  if (socket.connected) {
    socket.emit("get_available_rooms");
  } else {
    socket.on("connect", () => {
      socket.emit("get_available_rooms");
    });
  }
}

// Cập nhật danh sách phòng
function updateRoomsList(rooms) {
  if (!roomsList) return;
  
  roomsList.innerHTML = "";
  
  if (!rooms || rooms.length === 0) {
    const li = document.createElement("li");
    li.textContent = "Không có phòng nào";
    roomsList.appendChild(li);
    return;
  }
  
  rooms.forEach(room => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="room-item">
        <span class="room-name">${room.name}</span>
        <span class="room-id">${room.id}</span>
        <span class="room-players">${room.player_count}/${room.max_players}</span>
        <button class="btn-join-room" onclick="joinRoomById('${room.id}')">Tham gia</button>
      </div>
    `;
    roomsList.appendChild(li);
  });
}

// Tham gia phòng theo ID
function joinRoomById(roomId) {
  document.getElementById("room").value = roomId;
  currentRoom = roomId;
  joinExistingRoom();
}

// Copy mã phòng
async function copyRoomId() {
  const roomInput = document.getElementById("room");
  const roomId = roomInput.value.trim();
  
  if (!roomId) {
    showStatus("❌ Không có mã phòng để copy", "error", "join");
    return;
  }
  
  try {
    await navigator.clipboard.writeText(roomId);
    showStatus("✅ Đã copy mã phòng vào clipboard", "success", "join");
    
    // Thay đổi text tạm thời
    const originalText = copyRoomBtn.textContent;
    copyRoomBtn.textContent = "✅";
    setTimeout(() => {
      copyRoomBtn.textContent = originalText;
    }, 2000);
  } catch (err) {
    // Fallback cho các trình duyệt cũ
    roomInput.select();
    document.execCommand("copy");
    showStatus("✅ Đã copy mã phòng vào clipboard", "success", "join");
    
    // Thay đổi text tạm thời
    const originalText = copyRoomBtn.textContent;
    copyRoomBtn.textContent = "✅";
    setTimeout(() => {
      copyRoomBtn.textContent = originalText;
    }, 2000);
  }
}

// Rời phòng
function leaveRoom() {
  if (socket && socket.connected) {
    socket.emit("leave_room");
  }
  
  // Reset game state
  if (chatBox) chatBox.innerHTML = "";
  if (leaderboardList) leaderboardList.innerHTML = "";
  if (result) result.textContent = "";
  
  // Reset round info
  if (roundNumber) roundNumber.textContent = "1";
  if (rangeStart) rangeStart.textContent = "1";
  if (rangeEnd) rangeEnd.textContent = "100";
  
  // Quay về màn hình join
  gameScreen.classList.add("hidden");
  joinScreen.classList.remove("hidden");
  
  // Reset status
  if (joinStatus) {
    joinStatus.textContent = "";
    joinStatus.className = "status info";
  }
  
  console.log("🚪 Đã rời phòng:", currentRoom);
}

// ---- Core functions
function createRoom() {
  username = document.getElementById("username").value.trim() || "Khách";
  
  // Tạo mã phòng ngẫu nhiên
  const newRoomId = generateRoomId();
  const roomName = `Phòng của ${username}`;
  
  // Cập nhật input room với mã phòng mới
  document.getElementById("room").value = newRoomId;
  currentRoom = newRoomId;
  
  // Hiển thị thông báo đang tạo phòng với mã phòng
  showStatus(`🔄 Đang tạo phòng mới: ${newRoomId}...`, "info", "join");
  
  // Gửi event tạo phòng
  if (socket.connected) {
    socket.emit("create_room", {
      room_id: newRoomId,
      room_name: roomName,
      max_players: 10
    });
  } else {
    socket.on("connect", () => {
      socket.emit("create_room", {
        room_id: newRoomId,
        room_name: roomName,
        max_players: 10
      });
    });
  }
}

function joinExistingRoom() {
  username = document.getElementById("username").value.trim() || "Khách";
  currentRoom = document.getElementById("room").value.trim() || "lobby";

  // Hiển thị thông báo đang tham gia phòng
  showStatus(`🔄 Đang tham gia phòng: ${currentRoom}...`, "info", "join");

  // Ẩn màn hình join, hiện gameplay
  joinScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
  
  // Hiển thị game header và cập nhật mã phòng
  const gameheader = document.getElementById("gameheader");
  const roomValue = document.getElementById("roomValue");
  if (gameheader && roomValue) {
    gameheader.classList.remove("hidden");
    roomValue.textContent = currentRoom;
  }

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

// Event handler cho việc tạo phòng thành công
socket.on("room_created", (data) => {
  console.log("🎉 Tạo phòng thành công:", data);
  showStatus(`✅ Đã tạo phòng ${data.room_name} (${data.room_id})`, "success", "join");
  
  // Cập nhật mã phòng trong input nếu chưa có
  if (document.getElementById("room").value !== data.room_id) {
    document.getElementById("room").value = data.room_id;
    currentRoom = data.room_id;
  }
  
  // Cập nhật game header nếu đã hiển thị
  const roomValue = document.getElementById("roomValue");
  if (roomValue) {
    roomValue.textContent = data.room_id;
  }
  
  // Hiển thị mã phòng rõ ràng cho người dùng
  showStatus(`🎯 Mã phòng của bạn: ${data.room_id}`, "success", "join");
  
  // Tự động tham gia phòng vừa tạo sau 2 giây để người dùng thấy thông báo và mã phòng
  setTimeout(() => {
    joinExistingRoom();
  }, 2000);
});

// Event handler cho lỗi tạo phòng
socket.on("create_room_error", (data) => {
  console.log("❌ Lỗi tạo phòng:", data.error);
  showStatus(`❌ Lỗi tạo phòng: ${data.error}`, "error", "join");
  
  // Nếu lỗi do phòng đã tồn tại, tạo mã phòng mới
  if (data.error.includes("đã tồn tại") || data.error.includes("already exists")) {
    setTimeout(() => {
      showStatus("🔄 Đang thử tạo phòng mới...", "info", "join");
      createRoom();
    }, 2000);
  }
});

// Event handler cho danh sách phòng có sẵn
socket.on("available_rooms", (data) => {
  console.log("🏠 Danh sách phòng có sẵn:", data.rooms);
  updateRoomsList(data.rooms);
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
  showStatus(`✅ Đã tham gia phòng ${data.room_name || currentRoom} thành công!`, "success", "game");
  
  // Lưu trạng thái game
  saveGameState();
  
  // Cập nhật game header với mã phòng
  const roomValue = document.getElementById("roomValue");
  if (roomValue) {
    roomValue.textContent = data.room_id || currentRoom;
  }
  
  // Hiển thị thông tin phòng
  if (data.room_info) {
    // Hiển thị bảng điểm hiện tại
    if (data.room_info.scores) {
      updateLeaderboard(data.room_info.scores);
    }
    
    // Hiển thị thông tin vòng hiện tại
    if (data.room_info.current_round) {
      const round = data.room_info.current_round;
      const roundNum = data.room_info.round_number || "?";
      
      // Cập nhật UI với thông tin vòng hiện tại
      if (roundNumber) roundNumber.textContent = roundNum;
      if (rangeStart) rangeStart.textContent = round.range[0];
      if (rangeEnd) rangeEnd.textContent = round.range[1];
      
      showStatus(`🎮 Vòng ${roundNum}: Đoán số từ ${round.range[0]} đến ${round.range[1]}`, "info", "game");
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
  
  // Cập nhật UI với thông tin vòng mới
  if (roundNumber) roundNumber.textContent = roundNum;
  if (rangeStart) rangeStart.textContent = range[0];
  if (rangeEnd) rangeEnd.textContent = range[1];
  
  showStatus(`🎮 Vòng ${roundNum} bắt đầu! Đoán số từ ${range[0]} đến ${range[1]}`, "info", "game");
  
  // Reset result
  if (result) result.textContent = "";
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
  
  // Cập nhật UI với thông tin vòng
  if (roundNumber) roundNumber.textContent = roundId;
  if (rangeStart) rangeStart.textContent = range[0];
  if (rangeEnd) rangeEnd.textContent = range[1];
  
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
// Khôi phục trạng thái game khi trang load
document.addEventListener('DOMContentLoaded', () => {
  console.log("🔄 Đang khôi phục trạng thái game...");
  
  // Khởi tạo elements
  initializeElements();
  
  if (loadGameState()) {
    console.log("✅ Khôi phục trạng thái thành công:", { username, currentRoom });
    showStatus(`🔄 Đã khôi phục: ${username} trong phòng ${currentRoom}`, "info", "join");
    
    // Nếu có room parameter trong URL, tự động chuyển vào game
    if (room && room !== "lobby") {
      setTimeout(() => {
        joinExistingRoom();
      }, 1000);
    }
  }
});

// Khởi tạo elements và event listeners
function initializeElements() {
  // Cache elements
  joinBtn = document.getElementById("joinBtn");
  createBtn = document.getElementById("createBtn");
  joinScreen = document.getElementById("join-screen");
  gameScreen = document.getElementById("game-screen");
  chatBox = document.getElementById("chatBox");
  leaderboardList = document.getElementById("leaderboardList");
  result = document.getElementById("result");
  joinStatus = document.getElementById("joinStatus");
  
  // Thêm nút hiển thị danh sách phòng
  showRoomsBtn = document.getElementById("showRoomsBtn");
  roomsList = document.getElementById("roomsList");
  
  // Game elements
  leaveRoomBtn = document.getElementById("leaveRoomBtn");
  roundNumber = document.getElementById("roundNumber");
  rangeStart = document.getElementById("rangeStart");
  rangeEnd = document.getElementById("rangeEnd");
  
  // Copy elements
  copyRoomBtn = document.getElementById("copyRoomBtn");
  
  // Thêm event listeners
  if (joinBtn) joinBtn.addEventListener("click", joinExistingRoom);
  if (createBtn) createBtn.addEventListener("click", createRoom);
  if (showRoomsBtn) showRoomsBtn.addEventListener("click", toggleRoomsList);
  if (leaveRoomBtn) leaveRoomBtn.addEventListener("click", leaveRoom);
  if (copyRoomBtn) copyRoomBtn.addEventListener("click", copyRoomId);
  
  // Event listeners cho chat và game
  const sendChatBtn = document.getElementById("sendChat");
  const guessBtn = document.getElementById("guessBtn");
  const chatMsg = document.getElementById("chatMsg");
  const guessInput = document.getElementById("guessInput");
  const roomInput = document.getElementById("room");
  const usernameInput = document.getElementById("username");
  
  if (sendChatBtn) sendChatBtn.addEventListener("click", sendChat);
  if (guessBtn) guessBtn.addEventListener("click", makeGuess);
  if (chatMsg) chatMsg.addEventListener("keydown", (e) => e.key === "Enter" && sendChat());
  if (guessInput) guessInput.addEventListener("keydown", (e) => e.key === "Enter" && makeGuess());
  if (roomInput) roomInput.addEventListener("keydown", (e) => e.key === "Enter" && joinExistingRoom());
  if (usernameInput) usernameInput.addEventListener("keydown", (e) => e.key === "Enter" && roomInput.focus());
  
  console.log("✅ Đã khởi tạo elements và event listeners");
  
  // Auto-join if room parameter exists
  if (room && room !== "lobby") {
    console.log("📝 Phòng được chỉ định:", room);
    showStatus(`📝 Phòng được chỉ định: ${room}`, "info", "join");
  } else {
    console.log("🏠 Phòng mặc định: lobby");
    showStatus("🏠 Phòng mặc định: lobby", "info", "join");
  }
}

// Toggle danh sách phòng
function toggleRoomsList() {
  if (roomsList.classList.contains("hidden")) {
    roomsList.classList.remove("hidden");
    showRoomsBtn.textContent = "📋 Ẩn danh sách phòng";
    showAvailableRooms();
  } else {
    roomsList.classList.add("hidden");
    showRoomsBtn.textContent = "📋 Xem phòng có sẵn";
  }
}

// Gửi chat
function sendChat() {
  const msgInput = document.getElementById("chatMsg");
  const msg = msgInput.value;
  if (msg.trim() !== "" && socket && socket.connected) {
    socket.emit("chat_message", { 
      room_id: currentRoom, 
      message: msg 
    });
    msgInput.value = "";
  }
}

// Gửi đoán số
function makeGuess() {
  const v = document.getElementById("guessInput").value;
  const guess = parseInt(v, 10);
  if (!Number.isNaN(guess) && socket && socket.connected) {
    socket.emit("make_guess", { 
      room_id: currentRoom, 
      guess: guess 
    });
    document.getElementById("guessInput").value = "";
  }
}
