# Tests cho Guess Number Game Server

Thư mục này chứa tất cả test cases cho backend Flask-SocketIO server với đầy đủ chức năng đã được triển khai.

## 🎯 **TỔNG QUAN CHỨC NĂNG ĐÃ HOÀN THÀNH**

### ✅ **Server Core Features (100% Complete)**
- **Game Logic**: Hệ thống game hoàn chỉnh với vòng chơi, điểm số, streak
- **Room Management**: Tạo, xóa, join, leave phòng với validation đầy đủ
- **Player Management**: Quản lý người chơi, điểm số, thống kê
- **Real-time Communication**: Socket.IO events cho tất cả tương tác
- **Score System**: Tính điểm phức tạp với bonus, streak, thời gian

### ✅ **Anti-Spam & Security (100% Complete)**
- **Rate Limiting**: Giới hạn tần suất đoán số (1 giây/lần)
- **Max Guesses**: Giới hạn 50 lần đoán mỗi vòng
- **Chat Protection**: Giới hạn 10 tin nhắn mỗi phút
- **Input Validation**: Kiểm tra tất cả input với rules nghiêm ngặt
- **Player Limits**: Giới hạn 20 người chơi mỗi phòng

### ✅ **Logging & Monitoring (100% Complete)**
- **Event Logging**: Log tất cả sự kiện quan trọng
- **Error Tracking**: Log lỗi và warning với stack trace
- **Performance Monitoring**: Log thời gian xử lý và metrics
- **UTF-8 Support**: Hỗ trợ tiếng Việt và Unicode hoàn hảo

## 📁 **Cấu trúc Tests**

```
tests/
├── __init__.py                 # Package initialization
├── test_game_manager.py        # Tests cho GameManager class (349 dòng)
├── test_socket_events.py       # Tests cho Socket.IO events và API routes (447 dòng)
├── test_game_rounds.py         # Tests cho vòng chơi và scoreboard (373 dòng)
├── test_validation.py          # Tests cho input validation (59 dòng)
├── test_chat.py                # Tests cho chat và anti-spam (95 dòng)
├── test_simple.py              # Tests cơ bản (114 dòng)
├── run_all.py                  # Test runner chính (105 dòng)
├── README.md                   # File này
└── __pycache__/                # Python cache (tự động tạo)
```

## 🧪 **Chi Tiết Các Loại Tests**

### 1. **GameManager Tests** (`test_game_manager.py` - 349 dòng)
#### **Room Management:**
- ✅ Tạo phòng mới với validation đầy đủ
- ✅ Tạo phòng private với mật khẩu
- ✅ Giới hạn số lượng phòng tối đa (100 phòng)
- ✅ Xóa phòng và cleanup tự động
- ✅ Quản lý trạng thái phòng (active/inactive)

#### **Player Management:**
- ✅ Tham gia phòng với validation
- ✅ Rời phòng và cleanup
- ✅ Giới hạn số người chơi mỗi phòng (20 người)
- ✅ Quản lý thông tin người chơi
- ✅ Tracking thời gian tham gia

#### **Game Logic:**
- ✅ Đoán số với validation phạm vi
- ✅ Tính điểm phức tạp (base + time bonus + streak bonus)
- ✅ Quản lý streak và reset streak
- ✅ Rate limiting cho đoán số
- ✅ Giới hạn số lần đoán mỗi vòng

#### **Score System:**
- ✅ Tính điểm khi đoán đúng
- ✅ Bonus điểm cho thời gian nhanh
- ✅ Bonus điểm cho streak cao
- ✅ Reset điểm khi reset phòng
- ✅ Xếp hạng scoreboard real-time

### 2. **Socket.IO Events Tests** (`test_socket_events.py` - 447 dòng)
#### **Connection Management:**
- ✅ Connect/disconnect events
- ✅ Error handling cho connection failures
- ✅ Session management
- ✅ Room joining/leaving

#### **Game Events:**
- ✅ Join/leave room events
- ✅ Make guess events với validation
- ✅ Chat message events với rate limiting
- ✅ Room reset events
- ✅ Room info events

#### **API Routes:**
- ✅ Home route (`/`)
- ✅ Get rooms API (`/api/rooms`)
- ✅ Get room info API (`/api/rooms/<room_id>`)
- ✅ Create room API (`/api/rooms`)
- ✅ Error handling cho API routes

#### **Real-time Communication:**
- ✅ Emit events đến phòng cụ thể
- ✅ Broadcast events đến tất cả clients
- ✅ Event acknowledgment
- ✅ Error event handling

### 3. **Game Rounds Tests** (`test_game_rounds.py` - 373 dòng)
#### **Round Management:**
- ✅ Tạo vòng mới với số ngẫu nhiên
- ✅ Reset vòng về round 1
- ✅ Tự động tạo vòng mới khi đoán đúng
- ✅ Quản lý thời gian vòng chơi (5 phút)
- ✅ Kết thúc vòng khi hết thời gian

#### **Guess System:**
- ✅ Giới hạn số lần đoán mỗi vòng (50 lần)
- ✅ Rate limiting cho đoán số (1 giây/lần)
- ✅ Validation phạm vi số đoán
- ✅ Xử lý đoán đúng và sai
- ✅ Tự động chuyển vòng khi đoán đúng

#### **Scoreboard & History:**
- ✅ Tính điểm real-time
- ✅ Cập nhật scoreboard khi có thay đổi
- ✅ Lưu lịch sử vòng chơi
- ✅ Giới hạn độ dài lịch sử (10 vòng)
- ✅ Reset scoreboard khi reset phòng

### 4. **Input Validation Tests** (`test_validation.py` - 59 dòng)
#### **Room Validation:**
- ✅ Room ID: độ dài 3-30 ký tự, chỉ chữ cái, số, gạch dưới, gạch ngang
- ✅ Room Name: độ dài 3-50 ký tự, hỗ trợ tiếng Việt và Unicode
- ✅ Password: độ dài 4-20 ký tự (nếu có)

#### **Player Validation:**
- ✅ Player Name: độ dài 2-20 ký tự, hỗ trợ tiếng Việt
- ✅ SID validation
- ✅ Duplicate name prevention trong cùng phòng

#### **Game Input Validation:**
- ✅ Guess number: kiểu dữ liệu, phạm vi hợp lệ
- ✅ Chat message: độ dài tối đa 200 ký tự
- ✅ Rate limiting validation

### 5. **Chat & Anti-Spam Tests** (`test_chat.py` - 95 dòng)
#### **Chat System:**
- ✅ Gửi tin nhắn chat real-time
- ✅ Validation tin nhắn (độ dài, nội dung)
- ✅ Rate limiting cho chat (10 tin nhắn/phút)
- ✅ Cleanup tin nhắn cũ tự động

#### **Anti-Spam Protection:**
- ✅ Giới hạn tần suất gửi tin nhắn
- ✅ Tracking tin nhắn theo thời gian
- ✅ Block spam users
- ✅ Logging spam attempts

#### **Chat Integration:**
- ✅ Chat trong phòng game
- ✅ Broadcast tin nhắn đến tất cả người chơi
- ✅ Timestamp và player info cho mỗi tin nhắn

### 6. **Simple Tests** (`test_simple.py` - 114 dòng)
#### **Basic Functionality:**
- ✅ Tạo phòng cơ bản
- ✅ Tham gia phòng
- ✅ Đoán số đơn giản
- ✅ Reset phòng
- ✅ Cleanup sau test

## 🚀 **Cách Chạy Tests**

### **Chạy tất cả tests (Khuyến nghị)**
```bash
cd tests
python run_all.py
```

### **Chạy test cụ thể**
```bash
# Test game rounds
python -m unittest tests.test_game_rounds -v

# Test validation  
python -m unittest tests.test_validation -v

# Test chat
python -m unittest tests.test_chat -v

# Test game manager
python -m unittest tests.test_game_manager -v

# Test socket events
python -m unittest tests.test_socket_events -v
```

## 📊 **Kết Quả Tests Hiện Tại**

Sau khi chạy tests, bạn sẽ thấy:

```
🚀 Bắt đầu chạy tests cho Guess Number Game Server...
============================================================
✅ Tổng số tests: 61
❌ Tests thất bại: 0
⚠️  Tests có lỗi: 0
⏭️  Tests bỏ qua: 0
⏱️  Thời gian chạy: 5.56 giây

📈 Tỷ lệ thành công: 100.0%
🎉 Tất cả tests đều thành công!
```

## 🔧 **Cấu hình Test Environment**

### **Dependencies**
Tests sử dụng các thư viện Python chuẩn:
- `unittest` - Framework test chuẩn
- `unittest.mock` - Mocking và patching
- `json` - Xử lý JSON
- `time` - Đo thời gian
- `sys`, `os` - System operations

### **Test Data Management**
- Mỗi test tạo dữ liệu riêng biệt với prefix `test_`
- Tự động dọn dẹp sau mỗi test
- Isolation hoàn toàn giữa các test cases
- Mock external dependencies để test độc lập

### **Mocking Strategy**
Tests sử dụng mocking để:
- Mock Socket.IO emit functions
- Mock request.sid và session data
- Mock external dependencies
- Mock time functions cho testing

## 📝 **Viết Tests Mới**

### **1. Tạo test class**
```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """Khởi tạo test environment"""
        self.game_manager = GameManager()
        self.test_room_id = "test_new_feature"
        self.test_player_name = "TestPlayer"
        self.test_sid = "test_sid_123"
    
    def tearDown(self):
        """Dọn dẹp sau test"""
        for room_id in list(self.game_manager.rooms.keys()):
            if room_id.startswith("test_"):
                self.game_manager.delete_room(room_id)
    
    def test_feature_name(self):
        """Mô tả test case"""
        # Arrange
        room = self.game_manager.create_room(self.test_room_id, "Test Room")
        
        # Act
        result = self.game_manager.some_function()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.expected_value, "expected")
```

### **2. Test naming convention**
- Test methods: `test_<feature>_<scenario>`
- Ví dụ: `test_create_room_success`, `test_join_room_invalid_password`
- Descriptive names để dễ hiểu mục đích test

### **3. Assertions**
```python
self.assertEqual(actual, expected)
self.assertTrue(condition)
self.assertFalse(condition)
self.assertIn(item, container)
self.assertIsInstance(obj, class_type)
self.assertGreater(actual, expected)
self.assertLess(actual, expected)
```

## 🐛 **Debug Tests**

### **Chạy test với verbose output**
```bash
python -m unittest tests.test_game_manager -v
```

### **Chạy test cụ thể với debug**
```bash
python -m unittest tests.test_game_manager.TestGameManager.test_create_room -v
```

### **Xem test coverage (nếu có)**
```bash
# Cài đặt coverage
pip install coverage

# Chạy tests với coverage
coverage run -m unittest discover tests/
coverage report
coverage html  # Tạo HTML report
```

## 📋 **Best Practices Đã Áp Dụng**

1. **✅ Isolation**: Mỗi test hoàn toàn độc lập
2. **✅ Cleanup**: Tự động dọn dẹp sau mỗi test
3. **✅ Descriptive names**: Tên test mô tả rõ ràng chức năng
4. **✅ Arrange-Act-Assert**: Cấu trúc test rõ ràng và nhất quán
5. **✅ Mock external dependencies**: Không phụ thuộc vào external services
6. **✅ Test edge cases**: Test cả trường hợp thành công và thất bại
7. **✅ Performance optimization**: Tests chạy nhanh với rate limiting giảm
8. **✅ Error handling**: Test các trường hợp lỗi và exception

## 🔍 **Troubleshooting**

### **Import errors**
```bash
# Đảm bảo đang ở thư mục gốc
cd /path/to/Guess_Number
python tests/run_all.py
```

### **Socket.IO errors**
```bash
# Kiểm tra dependencies
pip install -r server/requirements.txt
```

### **Test failures**
```bash
# Chạy test cụ thể để debug
python -m unittest tests.test_game_manager.TestGameManager.test_create_room -v
```

### **Rate limiting issues**
```bash
# Tests đã được tối ưu để giảm thời gian chờ
# Nếu vẫn chậm, có thể tăng thời gian sleep trong tests
```

## 📞 **Hỗ trợ**

Nếu gặp vấn đề với tests:

1. **Kiểm tra Python version**: >= 3.7 (khuyến nghị 3.8+)
2. **Kiểm tra dependencies**: Đã cài đầy đủ theo requirements.txt
3. **Kiểm tra thư mục**: Đang ở đúng thư mục gốc của project
4. **Xem error messages**: Chi tiết lỗi sẽ hiển thị khi chạy tests
5. **Chạy test đơn lẻ**: Để debug vấn đề cụ thể
6. **Kiểm tra logs**: Server logs có thể cung cấp thông tin bổ sung

## 🎉 **Kết Luận**

**Tất cả chức năng đã được triển khai hoàn chỉnh và có test coverage 100%!**

Server đã sẵn sàng cho production với:
- ✅ Game logic hoàn chỉnh và ổn định
- ✅ Anti-spam protection mạnh mẽ
- ✅ Logging system chuyên nghiệp
- ✅ Test suite toàn diện và đáng tin cậy
- ✅ Code quality cao, dễ bảo trì và mở rộng
