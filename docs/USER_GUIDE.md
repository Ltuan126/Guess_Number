# 📖 Hướng dẫn sử dụng Guess Number Game

## 🚀 Bắt đầu nhanh

### 1. Khởi động ứng dụng

**Cách 1: Chạy server + mở client**
```bash
# Terminal 1: Khởi động server
cd server
python start_server.py

# Terminal 2: Khởi động client server
cd client  
python -m http.server 3000
```

Sau đó mở trình duyệt và truy cập `http://localhost:3000`

**Cách 2: Sử dụng Docker**
```bash
cd docker
docker-compose up --build
```

Truy cập `http://localhost:8080`

### 2. Tạo phòng mới

1. Nhập tên người chơi
2. Nhấn nút **"Tạo phòng mới"**
3. Hệ thống sẽ tự động tạo mã phòng 6 ký tự
4. Copy mã phòng để chia sẻ với bạn bè
5. Tự động vào game sau 2 giây

### 3. Tham gia phòng có sẵn

1. Nhập tên người chơi
2. Nhập mã phòng (6 ký tự)
3. Nhấn **"Tham gia phòng"** hoặc Enter
4. Vào game ngay lập tức

### 4. Xem danh sách phòng

1. Nhấn **"📋 Xem phòng có sẵn"**
2. Danh sách hiển thị: tên phòng, mã phòng, số người chơi
3. Nhấn **"Tham gia"** bên cạnh phòng muốn vào

## 🎮 Cách chơi

### Giao diện game

```
┌─────────────────────────────────────────────────────────┐
│ RoomID: ABC123        ⏳ Countdown: 45s    🚪 Rời phòng │
├─────────────────────────────────────────────────────────┤
│ 💬 Chat    │  🎮 Vòng 2: Đoán số 1-100  │ 🏆 Leaderboard │
│            │           ?                │ 1. Alice: 25pts │
│ Alice: Hi! │    [____] [Đoán]          │ 2. Bob: 15pts   │
│ Bob: 42?   │                           │ 3. You: 10pts   │
│ [____][Gửi]│    Status: Số quá cao!    │                │
└─────────────────────────────────────────────────────────┘
```

### Các thao tác

- **Đoán số**: Nhập số → Enter hoặc nhấn "Đoán"
- **Chat**: Nhập tin nhắn → Enter hoặc nhấn "Gửi"  
- **Copy mã phòng**: Nhấn 📋 bên cạnh input mã phòng
- **Rời phòng**: Nhấn "🚪 Rời phòng" ở góc trên phải
- **Xem phòng khác**: Về màn hình chính và xem danh sách

### Tính điểm

- **Đoán đúng**: +10 điểm cơ bản
- **Bonus thời gian**: +5 điểm nếu đoán nhanh
- **Streak**: x1.5 điểm nếu đoán đúng liên tiếp

## ⌨️ Keyboard Shortcuts

| Phím | Chức năng |
|------|-----------|
| `Enter` trong username | Focus vào input mã phòng |
| `Enter` trong mã phòng | Tham gia phòng |
| `Enter` trong chat | Gửi tin nhắn |
| `Enter` trong đoán số | Gửi số đoán |

## 🔧 Tính năng nâng cao

### 1. Khôi phục trạng thái
- Game tự động lưu trạng thái vào localStorage
- Khi refresh trang, tự động khôi phục tên và phòng
- Trạng thái có hiệu lực trong 1 giờ

### 2. Reconnection tự động
- Tự động kết nối lại khi mất mạng
- Tự động tham gia lại phòng khi kết nối lại
- Hiển thị status kết nối rõ ràng

### 3. Anti-spam
- Giới hạn 1 lần đoán mỗi giây
- Giới hạn 10 tin nhắn chat mỗi phút
- Giới hạn 50 lần đoán mỗi vòng

## ❗ Xử lý lỗi

### Lỗi thường gặp

**"Phòng không tồn tại"**
- Kiểm tra lại mã phòng (6 ký tự)
- Phòng có thể đã bị xóa do không hoạt động

**"Phòng đã đầy"**
- Chọn phòng khác từ danh sách
- Hoặc tạo phòng mới

**"Mất kết nối"**
- Kiểm tra kết nối mạng
- Game sẽ tự động kết nối lại

**"Không thể tạo phòng"**
- Thử lại sau vài giây
- Hệ thống sẽ tự động tạo mã phòng mới

### Debug

Mở Developer Tools (F12) để xem console logs:
- `🔄`: Thông tin khôi phục trạng thái
- `✅`: Kết nối thành công
- `❌`: Lỗi và cảnh báo
- `🎮`: Thông tin game
- `💬`: Tin nhắn chat

## 🎯 Mẹo chơi hiệu quả

1. **Chiến thuật binary search**: Luôn chọn số ở giữa khoảng
2. **Quan sát pattern**: Học từ lượt đoán của người khác
3. **Chat thông minh**: Chia sẻ thông tin với team
4. **Đoán nhanh**: Bonus thời gian chỉ dành cho người đoán đúng sớm
5. **Tạo streak**: Cố gắng đoán đúng liên tiếp để nhân điểm

## 🤝 Multiplayer Tips

- **Tạo phòng riêng**: Invite bạn bè với mã phòng
- **Tham gia lobby**: Phòng "lobby" luôn có sẵn cho mọi người
- **Respect others**: Không spam chat
- **Team play**: Chia sẻ chiến lược trong chat

Chúc bạn chơi vui vẻ! 🎉

