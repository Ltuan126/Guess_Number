// === game.js - Number Guessing Game Client ===
const params = new URLSearchParams(window.location.search);
const room = (params.get("room") || "lobby").trim();

// Socket.IO connection
const socket = io("http://localhost:5000", {
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 500,
});

let username;
let currentRoom = room;
let isAdmin = false;

// Save game state to localStorage
function saveGameState() {
  if (username && currentRoom) {
    const state = {
      username: username,
      room: currentRoom,
      timestamp: Date.now()
    };
    localStorage.setItem('guessNumberGame', JSON.stringify(state));
  }
}

// Load saved game state
function loadGameState() {
  try {
    const saved = localStorage.getItem('guessNumberGame');
    if (saved) {
      const state = JSON.parse(saved);
      // Check if state is still valid (not older than 1 hour)
      if (Date.now() - state.timestamp < 3600000) {
        username = state.username;
        currentRoom = state.room;
        
        // Update UI
        if (document.getElementById("username")) {
          document.getElementById("username").value = username;
        }
        if (document.getElementById("room")) {
          document.getElementById("room").value = currentRoom;
        }
        
        return true;
      }
    }
  } catch (e) {
    console.error("Error loading game state:", e);
  }
  return false;
}

// Generate random room ID
function generateRoomId() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// Cache DOM elements
let joinBtn, createBtn, joinScreen, gameScreen, chatBox, leaderboardList, result, joinStatus;
let showRoomsBtn, roomsList, leaveRoomBtn, roundNumber, rangeStart, rangeEnd, copyRoomBtn;
let roomsModal, createRoomModal, passwordGroup, roomPasswordInput;

// Show status messages
function showStatus(message, type = "info", target = "both") {
  if (target === "both" || target === "join") {
    if (joinStatus) {
      joinStatus.textContent = message;
      joinStatus.className = `status ${type}`;
    }
  }
  
  if (target === "both" || target === "game") {
    if (result) {
      result.textContent = message;
      result.className = `result-message ${type}`;
    }
  }
}

// Show available rooms
function showAvailableRooms() {
  if (socket.connected) {
    socket.emit("get_available_rooms");
  } else {
    socket.on("connect", () => {
      socket.emit("get_available_rooms");
    });
  }
}

// Update rooms list
function updateRoomsList(rooms) {
  if (!roomsList) return;
  
  roomsList.innerHTML = '';
  
  if (rooms.length === 0) {
    roomsList.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">Không có phòng nào có sẵn</p>';
    return;
  }
  
  rooms.forEach((room, index) => {
    
    const roomItem = document.createElement('div');
    roomItem.className = 'room-item';
    
    roomItem.innerHTML = `
      <div class="room-info">
        <span class="room-name">${room.name}</span>
        <div class="room-details">
          Mã: ${room.id} | ${room.current_players}/${room.max_players} người | Vòng ${room.round_number}
        </div>
      </div>
      <button class="join-room-btn" onclick="joinRoomFromList('${room.id}')">Tham gia</button>
    `;
    
    roomsList.appendChild(roomItem);
  });
}

// Join room from list
function joinRoomFromList(roomId) {
  
  // Get username from input instead of variable
  const usernameInput = document.getElementById("username");
  const playerName = usernameInput ? usernameInput.value.trim() : "";
  
  if (!playerName) {
    showStatus("Vui lòng nhập tên người chơi trước", "error", "join");
    return;
  }
  
  // Update room ID input value
  const roomInput = document.getElementById("room");
  if (roomInput) {
    roomInput.value = roomId;
  }
  
  // Update currentRoom variable
  currentRoom = roomId;
  
  // Call joinRoom function
  joinRoom();
  
  // Close rooms modal
  closeModal(roomsModal);
}

// Show modal
function showModal(modal) {
  if (modal) {
    modal.classList.remove('hidden');
  }
}

// Close modal
function closeModal(modal) {
  if (modal) {
    modal.classList.add('hidden');
  }
}

// Create new room
function createRoom() {
  
  const roomName = document.getElementById("room-name").value.trim();
  const customRoomId = document.getElementById("custom-room-id").value.trim();
  const maxPlayers = parseInt(document.getElementById("max-players").value);
  const password = document.getElementById("create-password").value.trim();
  
  if (!roomName) {
    showStatus("Vui lòng nhập tên phòng", "error", "join");
    return;
  }
  
  const roomId = customRoomId || generateRoomId();
  
  const roomData = {
    room_id: roomId,
    room_name: roomName,
    max_players: maxPlayers,
    password: password || null
  };
  
  socket.emit("create_room", roomData);
  
  closeModal(createRoomModal);
}

// Join room
function joinRoom() {
  
  const roomId = document.getElementById("room").value.trim();
  const playerName = document.getElementById("username").value.trim();
  
  if (!roomId || !playerName) {
    showStatus("Vui lòng nhập đầy đủ thông tin", "error", "join");
    return;
  }
  
  const password = roomPasswordInput ? roomPasswordInput.value : null;
  
  socket.emit("join_room", {
    room_id: roomId,
    player_name: playerName,
    password: password
  });
}

// Leave room
function leaveRoom() {
  
  socket.emit("leave_room");
  
  switchToJoinScreen();
}

// Switch to join screen
function switchToJoinScreen() {
  
  joinScreen.classList.remove("hidden");
  gameScreen.classList.add("hidden");
  
  // Reset game state
  username = "";
  currentRoom = "";
  isAdmin = false;
  
  // Clear inputs
  document.getElementById("username").value = "";
  document.getElementById("room").value = "";
  if (roomPasswordInput) roomPasswordInput.value = "";
  
  // Clear game data
  if (chatBox) chatBox.innerHTML = "";
  if (leaderboardList) leaderboardList.innerHTML = "";
  if (result) result.textContent = "";
  
  // Reset UI
  document.getElementById("round-number").textContent = "1";
  document.getElementById("range-start").textContent = "1";
  document.getElementById("range-end").textContent = "100";
  document.getElementById("total-guesses").textContent = "0";
  document.getElementById("game-status-text").textContent = "Đang chờ...";
  document.getElementById("countdown").textContent = "--";
  
}

// Switch to game screen
function switchToGameScreen() {
  
  joinScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
  
}

// Copy room ID
function copyRoomId() {
  
  if (currentRoom) {
    navigator.clipboard.writeText(currentRoom).then(() => {
      showStatus("Đã copy mã phòng vào clipboard!", "success", "game");
    }).catch(() => {
      showStatus("Không thể copy mã phòng", "error", "game");
    });
  }
}

// Make guess
function makeGuess() {
  
  const guessInput = document.getElementById("guess-input");
  const guess = parseInt(guessInput.value);
  
  if (isNaN(guess)) {
    showStatus("Vui lòng nhập số hợp lệ", "error", "game");
    return;
  }
  
  const guessData = {
    room_id: currentRoom,
    guess: guess
  };
  
  socket.emit("make_guess", guessData);
  
  guessInput.value = "";
}

// Send chat message
function sendChat() {
  
  const chatInput = document.getElementById("chat-msg");
  const message = chatInput.value.trim();
  
  if (!message) {
    return;
  }
  
  const chatData = {
    room_id: currentRoom,
    message: message
  };
  
  socket.emit("chat_message", chatData);
  
  chatInput.value = "";
}

// Reset room (only admin)
function resetRoom() {
  
  if (confirm("Bạn có chắc muốn reset phòng? Tất cả điểm số sẽ bị xóa.")) {
    
    const resetData = {
      room_id: currentRoom
    };
    
    socket.emit("reset_room", resetData);
  }
}

// Update leaderboard
function updateLeaderboard(scores) {
  if (!leaderboardList) return;
  
  leaderboardList.innerHTML = '';
  
  const sortedPlayers = Object.entries(scores)
    .sort(([,a], [,b]) => b - a)
    .map(([name, score], index) => ({ name, score, rank: index + 1 }));
  
  sortedPlayers.forEach((player, index) => {
    const li = document.createElement('li');
    li.innerHTML = `
      <span class="player-name">${player.name}</span>
      <span class="score">${player.score}</span>
      <span class="streak">#${player.rank}</span>
    `;
    leaderboardList.appendChild(li);
  });
}

// Update round info
function updateRoundInfo(data) {
  
  if (data.round_number) {
    document.getElementById("round-number").textContent = data.round_number;
  }
  
  if (data.range) {
    document.getElementById("range-start").textContent = data.range[0];
    document.getElementById("range-end").textContent = data.range[1];
  }
  
  if (data.end_time) {
    startCountdown(data.end_time);
  }
  
  // Reset số lần đoán về 0 khi bắt đầu vòng mới
  document.getElementById("total-guesses").textContent = "0";
}

// Start countdown
function startCountdown(endTime) {
  
  const countdownElement = document.getElementById("countdown");
  if (!countdownElement) return;
  
  const updateCountdown = () => {
    const now = Date.now();
    const timeLeft = Math.max(0, Math.floor((endTime - now) / 1000));
    
    if (timeLeft <= 0) {
      countdownElement.textContent = "Hết giờ!";
      countdownElement.style.color = "#dc3545";
      return;
    }
    
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    countdownElement.textContent = timeString;
    
    // Change color based on time left
    if (timeLeft <= 30) {
      countdownElement.style.color = "#dc3545"; // Red
    } else if (timeLeft <= 60) {
      countdownElement.style.color = "#ffc107"; // Yellow
    } else {
      countdownElement.style.color = "#28a745"; // Green
    }
    
    setTimeout(updateCountdown, 1000);
  };
  
  updateCountdown();
}

// Add chat message
function addChatMessage(data) {
  if (!chatBox) return;
  
  const messageDiv = document.createElement('div');
  messageDiv.className = 'chat-message';
  
  const now = new Date();
  const timeString = now.toLocaleTimeString('vi-VN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  
  messageDiv.innerHTML = `
    <span class="chat-time">${timeString}</span>
    <span class="chat-player">${data.player_name}:</span>
    <span class="chat-text">${data.message}</span>
  `;
  
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
  
}

// Update online count
function updateOnlineCount(count) {
  
  const onlineCountElement = document.getElementById("online-count");
  if (onlineCountElement) {
    onlineCountElement.textContent = `${count} người`;
  }
}

// Handle guess result
function handleGuessResult(data) {
  
  // Cập nhật số lần đoán
  if (data.details && data.details.total_guesses !== undefined) {
    document.getElementById("total-guesses").textContent = data.details.total_guesses;
  }
  
  if (data.details && data.details.correct) {
    // Correct guess
    showStatus(data.message, "success", "game");
    
    // Display score info
    const scoreInfo = `
      🎉 +${data.details.score_gained} điểm
      ${data.details.time_bonus > 0 ? `(Time bonus: +${data.details.time_bonus})` : ''}
      ${data.details.streak_bonus > 0 ? `(Streak bonus: +${data.details.streak_bonus})` : ''}
      Streak: ${data.details.streak}
    `;
    
    setTimeout(() => {
      showStatus(scoreInfo, "info", "game");
    }, 2000);
    
  } else {
    // Incorrect guess
    showStatus(data.message, "info", "game");
  }
}

// Socket.IO event handlers
socket.on("connect", () => {
  showStatus("Đã kết nối với server", "success", "join");
});

socket.on("disconnect", () => {
  showStatus("Mất kết nối với server", "error", "join");
});

socket.on("connected", (data) => {
});

socket.on("room_created", (data) => {
  showStatus(`Phòng ${data.room_id} đã được tạo thành công!`, "success", "join");
  
  // Auto-join the newly created room
  currentRoom = data.room_id;
  document.getElementById("room").value = data.room_id;
  
  if (username) {
    joinRoom();
  }
});

socket.on("room_joined", (data) => {
  
  username = data.player_name;
  currentRoom = data.room_id;
  
  // Update UI - check for room_info safety
  if (data.room_name) {
    document.getElementById("room-name-display").textContent = data.room_name;
  }
  
  if (data.room_info) {
    if (data.room_info.round_number) {
      document.getElementById("round-number").textContent = data.room_info.round_number;
    }
    
    if (data.room_info.current_round) {
      if (data.room_info.current_round.range && data.room_info.current_round.range.length >= 2) {
        document.getElementById("range-start").textContent = data.room_info.current_round.range[0];
        document.getElementById("range-end").textContent = data.room_info.current_round.range[1];
      }
      
      if (data.room_info.current_round.end_time) {
        startCountdown(data.room_info.current_round.end_time);
      }
    }
    
    // Update leaderboard
    if (data.room_info.scores) {
      updateLeaderboard(data.room_info.scores);
    }
    
    // Update online count
    if (data.room_info.current_players !== undefined) {
      updateOnlineCount(data.room_info.current_players);
    }
  } else {
    console.warn("No room_info from server");
  }
  
  // Switch to game screen
  switchToGameScreen();
  
  // Save state
  saveGameState();
});

socket.on("join_error", (data) => {
  showStatus(data.error, "error", "join");
});

socket.on("player_joined", (data) => {
  addChatMessage({
    player_name: "Hệ thống",
    message: `${data.player_name} đã tham gia phòng`
  });
  
  // Update online count - check for safety
  if (data.room_info && typeof data.room_info.current_players !== 'undefined') {
    updateOnlineCount(data.room_info.current_players);
  } else {
    console.warn("No room_info to update online count");
  }
});

socket.on("player_left", (data) => {
  addChatMessage({
    player_name: "Hệ thống",
    message: `${data.player_name} đã rời phòng`
  });
  
  // Update online count - check for safety
  if (data.room_info && typeof data.room_info.current_players !== 'undefined') {
    updateOnlineCount(data.room_info.current_players);
  } else {
    console.warn("No room_info to update online count");
  }
});

socket.on("new_round", (data) => {
  
  updateRoundInfo(data);
  
  addChatMessage({
    player_name: "Hệ thống",
    message: data.message
  });
  
  // Reset result message
  if (result) {
    result.textContent = "";
    result.className = "result-message";
  }
  
  // Reset guess input
  const guessInput = document.getElementById("guess-input");
  if (guessInput) {
    guessInput.value = "";
    guessInput.placeholder = `Nhập số từ ${data.range[0]} đến ${data.range[1]}`;
  }
});

socket.on("guess_result", (data) => {
  handleGuessResult(data);
});

socket.on("guess_error", (data) => {
  showStatus(data.error, "error", "game");
});

socket.on("chat_message", (data) => {
  addChatMessage(data);
});

socket.on("chat_error", (data) => {
  showStatus(data.error, "error", "game");
});

socket.on("scoreboard_updated", (data) => {
  updateLeaderboard(data.scores);
});

socket.on("room_reset", (data) => {
  showStatus(data.message, "info", "game");
  
  // Reset UI
  document.getElementById("round-number").textContent = "1";
  document.getElementById("total-guesses").textContent = "0";
  if (result) result.textContent = "";
  
  addChatMessage({
    player_name: "Hệ thống",
    message: "Phòng đã được reset, bắt đầu vòng mới!"
  });
});

socket.on("available_rooms", (data) => {
  updateRoomsList(data.rooms);
});

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  
  // Cache elements
  joinBtn = document.getElementById("joinBtn");
  createBtn = document.getElementById("createBtn");
  joinScreen = document.getElementById("join-screen");
  gameScreen = document.getElementById("game-screen");
  chatBox = document.getElementById("chat-box");
  leaderboardList = document.getElementById("leaderboard-list");
  result = document.getElementById("result");
  joinStatus = document.getElementById("join-status");
  
  // Modal elements
  roomsModal = document.getElementById("rooms-modal");
  createRoomModal = document.getElementById("create-room-modal");
  passwordGroup = document.getElementById("password-group");
  roomPasswordInput = document.getElementById("room-password");
  
  // Game elements
  showRoomsBtn = document.getElementById("showRoomsBtn");
  roomsList = document.getElementById("rooms-list");
  leaveRoomBtn = document.getElementById("leave-room-btn");
  copyRoomBtn = document.getElementById("copy-room-btn");
  roundNumber = document.getElementById("round-number");
  rangeStart = document.getElementById("range-start");
  rangeEnd = document.getElementById("range-end");
  
  // Event listeners
  if (joinBtn) {
    joinBtn.addEventListener("click", joinRoom);
  }
  
  if (createBtn) {
    createBtn.addEventListener("click", () => showModal(createRoomModal));
  }
  if (showRoomsBtn) {
    showRoomsBtn.addEventListener("click", () => {
      showAvailableRooms();
      showModal(roomsModal);
    });
  }
  
  // Modal close buttons
  const closeRoomsBtn = document.getElementById("closeRoomsBtn");
  const closeCreateBtn = document.getElementById("closeCreateBtn");
  const cancelCreateBtn = document.getElementById("cancelCreateBtn");
  
  if (closeRoomsBtn) {
    closeRoomsBtn.addEventListener("click", () => closeModal(roomsModal));
  }
  
  if (closeCreateBtn) {
    closeCreateBtn.addEventListener("click", () => closeModal(createRoomModal));
  }
  
  if (cancelCreateBtn) {
    cancelCreateBtn.addEventListener("click", () => closeModal(createRoomModal));
  }
  
  // Create room confirmation
  const confirmCreateBtn = document.getElementById("confirmCreateBtn");
  if (confirmCreateBtn) {
    confirmCreateBtn.addEventListener("click", createRoom);
  }
  
  // Game controls
  const guessBtn = document.getElementById("guess-btn");
  const sendChatBtn = document.getElementById("send-chat");
  const resetRoomBtn = document.getElementById("reset-room-btn");
  const refreshScoresBtn = document.getElementById("refresh-scores-btn");
  
  if (guessBtn) {
    guessBtn.addEventListener("click", makeGuess);
  }
  
  if (sendChatBtn) {
    sendChatBtn.addEventListener("click", sendChat);
  }
  
  if (resetRoomBtn) {
    resetRoomBtn.addEventListener("click", resetRoom);
  }
  
  if (refreshScoresBtn) {
    refreshScoresBtn.addEventListener("click", () => {
      if (currentRoom) {
        socket.emit("get_room_info", { room_id: currentRoom });
      }
    });
  }
  
  // Room management
  if (leaveRoomBtn) {
    leaveRoomBtn.addEventListener("click", leaveRoom);
  }
  
  if (copyRoomBtn) {
    copyRoomBtn.addEventListener("click", copyRoomId);
  }
  
  // Keyboard shortcuts
  const guessInput = document.getElementById("guess-input");
  const chatInput = document.getElementById("chat-msg");
  
  if (guessInput) {
    guessInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") makeGuess();
    });
  }
  
  if (chatInput) {
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") sendChat();
    });
  }
  
  // Update username when user types
  const usernameInput = document.getElementById("username");
  if (usernameInput) {
    usernameInput.addEventListener("input", (e) => {
      username = e.target.value.trim();
    });
  }
  
  // Load saved game state
  loadGameState();
  
});
